import time
import uuid

from flask import Flask, render_template, flash, request, jsonify, g, url_for, redirect, send_file  # ,make_response, session, current_app,
from flask_login import LoginManager, login_required, current_user, login_user, logout_user

from FudgeC2.Implant.Implant import ImplantSingleton
from FudgeC2.ServerApp.modules.UserManagement import UserManagementController
from FudgeC2.ServerApp.modules.StagerGeneration import StagerGeneration
from FudgeC2.ServerApp.modules.ImplantManagement import ImplantManagement
from FudgeC2.ServerApp.modules.ApplicationManager import AppManager

Imp = ImplantSingleton.instance
UsrMgmt = UserManagementController()
ImpMgmt = ImplantManagement()
StagerGen = StagerGeneration()
AppManager = AppManager()

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = str(uuid.uuid4())
login = LoginManager(app)
login.init_app(app)

# TODO: Controller dev work.
listener_management = None


# -- Context Processors --#
@app.context_processor
def inject_dict_for_all_auth_templates():
    # -- Returns the list of Campaigns the authenticated user has at least read access to
    if current_user.is_authenticated:
        return dict(campaignlist=UsrMgmt.campaign_get_user_campaign_list(current_user.user_email))
    else:
        return dict()


@app.context_processor
def inject_dict_for_all_campaign_templates():
    if 'cid' in g:
        cid = g.get('cid')
        campaign_name = AppManager.campaign_get_campaign_name_from_cid(cid)
        if cid is not None:
            return dict(campaign=campaign_name, cid=cid)
    return dict()


# -- Managing the error and user object. -- #
# ----------------------------------------- #
@login.user_loader
def load_user(user):
    return UsrMgmt.get_user_object(user)


@app.before_request
def before_request():
    return


@app.after_request
def add_header(r):
    return r


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('BaseHomePage'), 302)  # This should be a proper 404?


@app.errorhandler(401)
def page_not_found(e):
    return redirect(url_for('login'), 302)


# -- Authentication endpoints -- #
# ------------------------------ #
@app.route("/auth/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        if 'email' in request.form and 'password' in request.form and request.form['email'] != None and request.form['password'] != None:
            UserObject = UsrMgmt.user_login(request.form['email'],request.form['password'])
            if UserObject == False:
                return render_template("auth/LoginPage.html", error="Incorrect Username/Password")
            if UserObject.first_logon == 1:
                login_user(UserObject)
                return redirect(url_for("BaseHomePage"))
            else:
                guid = UsrMgmt.get_first_logon_guid(request.form['email'])
                return render_template("auth/PasswordResetPage.html",guid=guid)
    return render_template("auth/LoginPage.html")

@app.route("/auth/logout")
@login_required
def logout():
    if (current_user.is_authenticated):
        logout_user()
        return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))

@app.route("/auth/passwordreset", methods=['GET', 'POST'])
def PasswordReset():

    if request.method =="POST":
        UserObject = UsrMgmt.change_password_first_logon(request.form)
        if UserObject is not False:
            login_user(UserObject)
            return redirect(url_for('BaseHomePage'))
    return redirect(url_for('login'))


# -- JSON Response for command responses and waiting commands -- #
# -------------------------------------------------------------- #
# TODO: Replace JSON enpoints with websockets.


@app.route("/<cid>/cmd_response", methods=['GET', 'POST'])
@login_required
def cmdreturn(cid):
    # -- Javascript appears to not be printing out all entries
    if UsrMgmt.campaign_get_user_access_right_cid(current_user.user_email, cid):
        return jsonify(Imp.Get_CommandResult(cid))
    else:
        return str(0)


@app.route("/<cid>/waiting_commands", methods=['GET', 'POST'])
@login_required
def waitingcommands(cid):
    # -- Get JSON blob which contains all implant commands and then registration state
    commands = ImpMgmt.Get_RegisteredImplantCommands(current_user.user_email, cid)
    return jsonify(commands)


# -- Main endpoints -- #
# -------------------- #
@app.route("/")
@login_required
def BaseHomePage():
    return render_template("Homepage.html",
                           out_of_date=AppManager.check_software_version(),
                           version_number=AppManager.get_software_verision_number())


@app.route("/CreateCampaign", methods=['GET', 'POST'])
@login_required
def create_new_campaign():
    if request.method == "POST":
        success_bool, success_msg = AppManager.campaign_create_campaign(current_user.user_email, request.form)
        if success_bool is True:
            return redirect(url_for('BaseHomePage'))
        else:
            return render_template('CreateCampaign.html', error=success_msg)
    return render_template('CreateCampaign.html')


@app.route("/settings", methods=['GET', 'POST'])
@login_required
def global_settings_page():
    if request.method == "POST":
        # -- Add user returns a dict with action/result/reason keys.
        result = UsrMgmt.add_new_user(request.form, current_user.user_email)
        return jsonify(result)
    logs = AppManager.get_application_logs(current_user.user_email)
    return render_template("settings/GlobalSettings.html", logs=logs)


@app.route("/listener", methods=['GET', 'POST'])
@login_required
def GlobalListenerPage():
    if app.config['listener_management'].check_tls_certificates() is False:
        flash('TLS certificates do not exist within the <install dir>/FudgeC2/Storage directory.')
    return render_template("listeners/listeners.html", test_data=app.config['listener_management'].get_active_listeners())


@app.route("/listener/change", methods=['GET', 'POST'])
@login_required
def Listener_Updates():
    if request.method == "POST":
        print(request.form)
        form_response = app.config['listener_management'].listener_form_submission(current_user.user_email, request.form)
        flash(form_response[1])
        return redirect(url_for('GlobalListenerPage'))

# -- CAMPAIGN SPECIFIC PAGES -- #
# ----------------------------- #

@app.route("/<cid>/")
@login_required
def BaseImplantPage(cid):
    # Returns the implant interaction page if any implant templates exist.
    g.setdefault('cid', cid)
    implant_list = UsrMgmt.campaign_get_all_implant_base_from_cid(current_user.user_email, cid)
    if implant_list is not False:
        if len(implant_list) > 0:
            return render_template("implant_input.html", Implants=implant_list)

    msg = "No implants have called back in association with this campaign - create an implant base and use the stager page."
    return render_template("ImplantMain.html", cid=cid, Msg=msg)



@app.route("/<cid>/settings", methods=['GET', 'POST'])
@login_required
def BaseImplantSettings(cid):
    # Allows updating the permissions of users in a campaign, and the visualisation of allowed users.
    g.setdefault('cid', cid)
    if request.method == "POST":
        UsrMgmt.AddUserToCampaign(current_user.user_email, request.form, cid)
        return redirect(url_for('BaseImplantSettings', cid=cid))
    else:
        users = UsrMgmt.get_current_campaign_users_settings_list(current_user.user_email, cid)
        return render_template("settings/CampaignSettings.html", users=users)


@app.route("/<cid>/implant/create", methods=['GET', 'POST'])
@login_required
def NewImplant(cid):
    # -- set SID and user DB to convert --#
    g.setdefault('cid', cid)
    if request.method == "POST":
        result, result_text = ImpMgmt.CreateNewImplant(cid, request.form, current_user.user_email)
        if result is True:
            return render_template('CreateImplant.html', success=result_text)
        else:
            return render_template('CreateImplant.html', error=result_text)
    return render_template('CreateImplant.html')


# -- This may no longer be required -- #
@app.route("/<cid>/implant/generate", methods=["GET", "POST"])
@login_required
def ImplantGenerate():
    # -- Get iid from the POST request
    return "405"


@app.route("/<cid>/implant/cmd", methods=["GET", "POST"])
@login_required
def ImplantCmdRegister(cid):
    # -- GET FORM --#
    # --    if ALL register on all implants wiht user write authority
    # --    if <iid> check user write authority
    # --     else RETURN 501 && log error.
    print(request.form)
    return "404"


@app.route("/<cid>/implant/stagers", methods=["GET", "POST"])
@login_required
def ImplantStager(cid):
    g.setdefault('cid', cid)
    # -- get request: return list of implants --
    # -- Will update to a dropdown when exporting Word docs etc is possible -- #
    if request.method == "POST":
        if 'id' in request.args:
            try:
                if int(request.args['id']):
                    print("this is int")
            except:
                print("error")
        # TODO: Replace with content from webpage request.
        return send_file(StagerGen.GenerateSingleStagerFile(cid, current_user.user_email,"docx"), attachment_filename='file.docx')
    return render_template("ImplantStagerPage.html", implantList=StagerGen.GenerateStaticStagers(cid, current_user.user_email))


@app.route("/<cid>/implant/status", methods=['GET', 'POST'])
@login_required
def get_active_implant_status(cid):
    # This creates a JSON object which contains all the status of every activated implant.
    active_implant_list = UsrMgmt.campaign_get_all_implant_base_from_cid(current_user.user_email, cid)
    data = {}
    count = 1
    for implant in active_implant_list:
        implant_status_obj = {"status": None,
                              "title": implant['generated_title'],
                              "last_checked_in": implant['last_check_in']
                              }
        beacon = implant['beacon']
        time_from_last_check_in = time.time() - implant['last_check_in']

        if time_from_last_check_in < beacon * 1.5:
            implant_status_obj['status'] = "good"
        elif time_from_last_check_in < beacon * 2.5:
            implant_status_obj['status'] = "normal"
        else:
            implant_status_obj['status'] = "poor"

        data[count] = implant_status_obj
        count = count + 1
    return jsonify(data)


@app.route("/<cid>/graphs", methods=['GET', 'POST'])
@login_required
def CampaignGraph(cid):
    g.setdefault('cid', cid)
    # -- If we receive a POST request then we will populate the page, this will be called AFTER the page has loaded.
    if request.method=="POST":
        blah = {'a':"1",'b':"v"}
        return jsonify(blah)
    return render_template("CampaignGraph.html")


@app.route("/<cid>/logs", methods=["GET", "POST"])
@login_required
def CampaignLogs(cid):
    g.setdefault('cid',cid)
    if request.method == "POST":
        # -- Replace with pre-organised campaign logs - simplifies JS component.
        # Get_CampaignLogs
        return jsonify(ImpMgmt.Get_CampaignLogs(current_user.user_email, cid))
    return render_template("CampaignLogs.html")


# -- Implant command execution -- #
@app.route("/<cid>/implant/register_cmd", methods=["POST"])
@login_required
def ImplantCommandRegistration(cid):
    if request.method == "POST":
        # print("\nCID: ", cid, "\nFRM: ",request.form)
        # -- This is the new format using ImpMgmt to handle validation of user and command.
        registration_response = ImpMgmt.ImplantCommandRegistration(cid, current_user.user_email, request.form)
        # -- Currently no return value is required. This should be defined.
        # print(registration_response)
        return jsonify(registration_response)
    return "000"


@app.route("/help", methods=["GET"])
@login_required
def HelpPage():
    return render_template("HelpPage.html")


# TODO: Remove in production builds.
# @app.route("/test", methods = ['GET','POST'])
# def test_endpoint():
#     if request.method == "POST":
#         print(request.form)
#         #ImpMgmt.Demo_CreateNewImplant(1, request.form,current_user.user_email)
#
#     return render_template("Demo_CreateImplant.html")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
    print("App running")