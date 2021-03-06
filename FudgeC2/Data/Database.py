import bcrypt
import ast

# SQLAlchemy imports
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

# FudgeC2 imports
from FudgeC2.Data.models import Users, ResponseLogs, Implants, ImplantLogs, Campaigns, CampaignUsers, GeneratedImplants, AppLogs, CampaignLogs
from FudgeC2.Storage.settings import Settings
from FudgeC2.Data.CampaignLogging import CampaignLoggingDecorator

# Extended database classes.
from FudgeC2.Data.DatabaseUser import DatabaseUser
from FudgeC2.Data.DatabaseCampaign import DatabaseCampaign
from FudgeC2.Data.DatabaseImplant import DatabaseImplant

CL = CampaignLoggingDecorator()


class Database:
    def __init__(self):
        engine = create_engine("sqlite:///Storage/{}?check_same_thread=False".format(Settings.database_name))
        self.selectors = {
            "uid": Users.uid,
            "email": Users.user_email
        }
        self.Session = scoped_session(sessionmaker(bind=engine, autocommit=False))
        """:type: sqlalchemy.orm.Session"""  # PyCharm type fix. Not required for execution.

        self.user = DatabaseUser(self, self.Session)
        self.campaign = DatabaseCampaign(self, self.Session)
        self.implant = DatabaseImplant(self, self.Session)

        self.__does_admin_exist()

    # -- PRIVATE METHODS -- #
    def __get_userid__(self, email):
        # -- Require further improvement i.e try:catch
        query = self.Session.query(Users.uid).filter(Users.user_email == email).first()
        if query is None:
            return False
        else:
            return query[0]
        # TODO: Improve and avoid race conditions.

    def __get_user_object_from_email__(self, email):
        return self.Session.query(Users).filter(Users.user_email == email).first()

    # TODO: Remove method.
    def __get_campaignid__(self, campaign):
        # TODO: Improve the Try/Catch
        q = self.Session.query(Campaigns.cid).filter(Campaigns.title == campaign).first()
        if q is None:
            return False
        else:
            print(q[0])

    @staticmethod
    def __splice_implants_and_generated_implants__(obj):
        # Hand a list of genrerated imaplnts and implabt list pairs and splice
        #    them togerther returning in a [{},{}] format
        completed_list = []
        if type(obj) == list:
            for x in obj:
                result_of_splice = {}
                if str(type(x)) == "<class 'sqlalchemy.util._collections.result'>":
                    # print(x[0].__dict__,x[1].__dict__)
                    # b = x.__dict__
                    # if '_sa_instance_state' in b:
                    #     del b['_sa_instance_state']
                    result_of_splice = {**x[0].__dict__, **x[1].__dict__}
                completed_list.append(result_of_splice)
            return completed_list
        else:
            result_of_splice = {}
            if str(type(obj)) == "<class 'sqlalchemy.util._collections.result'>":
                result_of_splice = {**obj[0].__dict__, **obj[1].__dict__}
            completed_list.append(result_of_splice)
        return completed_list

    # TODO: REMOVE/Comment
    @staticmethod
    def __hash_cleartext_password__(password):
        # Hashed a clear text password ready for insertion into the database
        password_bytes = password.encode()
        hashedpassword = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        if bcrypt.checkpw(password_bytes, hashedpassword):
            return hashedpassword
        else:
            return False

    def __does_admin_exist(self):
        # -- Checking for admin existance, for first-time launches.
        if not self.__get_userid__("admin"):
            print("Creating first-time admin account.")
            if not self.user.add_new_user("admin", "letmein", True):
                raise ValueError("Error creating admin account in empty database.")

    # -- App Logging Classes -- #
    # ------------------------- #
    # -- This is called by the decorator, and it should be placed there too?

    def Log_ApplicationLogging(self, values):
        campaign = AppLogs(type=values['type'], data=values['data'])
        self.Session.add(campaign)
        try:
            self.Session.commit()  # flush check if this will work...
        except Exception as e:
            print(e)
            return False

    def Log_CampaignAction(self, dict_of_stuff):
        # print("Logging data")
        try:
            logs = CampaignLogs(
                user=dict_of_stuff['user'],
                campaign=dict_of_stuff['campaign'],
                time=dict_of_stuff['time'],
                log_type=dict_of_stuff['log_type'],
                entry=str(dict_of_stuff['entry'])
            )
            self.Session.add(logs)
            self.Session.commit()
            # print("Log: Log_CampaignAction::"+dict_of_stuff['log_type']+" success.")
            return True
        except Exception as e:
            print(e)
            return False

    # Used by WebApp to display the campaign logs.
    def Log_GetCampaignActions(self, cid):
        result = self.Session.query(CampaignLogs).filter(CampaignLogs.campaign == cid).all()
        ret_dict = {}

        for count, row in enumerate(result):
            ret_dict[count] = row.__dict__
            del ret_dict[count]['_sa_instance_state']
            ret_dict[count]['entry'] = ast.literal_eval(ret_dict[count]['entry'])
        return ret_dict

    def app_logging(self, log_type, message):
        # -- place holder function for application level logging.
        log = AppLogs(type=log_type, data=message)
        self.Session.add(log)
        self.Session.commit()
        return

    def get_application_logs(self):
        data = self.Session.query(AppLogs).all()
        return data
