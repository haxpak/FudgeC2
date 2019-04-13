# Fudge Overview
A Powershell implant framework built on Python3/Flask- Designed for team collaboration and client interaction and campaign timelining.

## Setup
### Installation

The simplest route to get a basic Fudge server up and running is:

```
git clone https://github.com/Ziconius/Fudge
cd Fudge
pip3 install -r requirements.txt
sudo ptyhon3 Controller.py
```

Depending on your connections, you will likely need to configure a number of proxy and routing servers. The most common configuration and set up is to use Fudge with HTTPS using a reverse NGINX/Apache2 proxy.

#### First Login
After the initial installation you can log in with the default admin account using the credentiasl: `admin:letmein`. You will be prompted to the admin password as this point. 

## Users
Users within Fudge are devided into 2 groups, admins and standard users. Admins have all of the usual functionality, such as user creation, and are required to create a new campaign.

Within campaign a users permissions can be configured to either have None/Read/Read+Write. Without read permissions, a user will not be able to see the existance of a campaign, nor will they be able to read implant responses, or registered commands.

Users with write permissions will be able to create implant templates, and execute commands on all active implants.

#### User configuration

An admin can create a new user from within the Global Settings options. They will have the option to set the user up with admin privileges.


## Campaigns
#### What is a campaign?
A campaign is a method of organising a red team, which allows access control to be applies at a per user/per implant basis

Each campaign contains a unique name and, implants, and logs while a user can be a member of multiple campaigns



## Implants

Implants are broken down into 3 areas

* Implant Templates
* Stagers
* Active Implants

### Implant Templates
An implant template is the what we will create to generate our stagers. The implant template wil contain the default configuration for an implant. Once the stager has been triggered and an active implant is running on the host this can be changed.

The list of default configurations are:
* URL
* Initial callback delay
* Port (where applicable)
* Beacon delay
* Protocols to use
  * HTTP
  * DNS
  * Binary
  
Once a template has been created the stager options will be displayed in the Campaign Stagers page.

### Stagers

The stagers are small, hard to identify scripts/macros etc which are responsible for downloaded and executing the full implant.

_Currently the only supported stager is utilises IEX and IWR to load the implant inot memory after downloading over HTTP._

### Active Implant

Active implants are the result of new stagers connecting. When a stager connects backt ot the C2 server a new implant is generated, and delivered to the target host. Each new stager check in create a new active implant entry.

##### _Example_
As part of a campaign an user creates an implant template called "Moozle Implant" which is delivery to a HR department in via word macro. This then results in five successful execution of the macro stager; as a result the user will see five active implants.
 
 These will be listed on the campaigns main implant page, with a six character unique blob. The unique implants will be listed something similar to below:

```
Moozle Implant_123459
Moozle Implant_729151
Moozle Implant_182943
Moozle Implant_613516
Moozle Implant_810021
```

Each of these implants can be individually interacted with, or using the "ALL" keyword to register a command against all active implants.



#### Implant configuration further info.
URL: An implant will be configured to call back to a given URL, or IP address.

Beacon time: [Default: 15 minutes] This is the time inbetween the implant calling back to the C2 server. Once an implant has been deployed it is possible to dynamically set this.

Protocols: A user will also need to select the protocols which the implant uses, the defaults are

* HTTP
* DNS 
* Binary protocol

A user can enable and disable protocols depending on the environment they believe they are working in.

Once an implant has been generated the Stagers page will provide a number of basic techniques which can be used to compromise the target. Currently stager techniques are as follows:

* IEX
* Windows Words Macro (In development)

### Active Development
Below is an high-level overview of the on-going development to increase functionality, and reliablility of Fudge.
#### Implant Manager Web App
* Add help page with implant special tags using `::cmd::` format.
* Order implant check-ins buy quality
* Review how implant responses are displayed within the main campaign page to improve readability
* Create log page with detailed logging of for each implant, including time, command, implant, pickup, and pickup time.
* Fill chronological graph page with real data.
* Create admin-only campaign extract function, encrypting with AES256. This require viewer tool.


##### Implant

* Add further work on implant obfuscation levels/configuration.
* Add implant special tags formatted: `::cmd::`
* Create further staging options (docx, pfd, etc)



##### Controller
* Check for `fudge.db` in the working dir, if not configure new setup.
* Code refactor Controller to boot server & listener 
* Restructure how listeners are configured and launched. This piece of work will likely take several weeks of re-engineering.
  

###  ----------------------