# Dashboard README
Hey there, thanks for looking at my dashboard!  This cog allows for you (the owner) to control your bot through a web dashboard, easily.  This can also be used for other people using the dashboard as well, as the dashboard uses Discord OAuth to log you in, and to make sure it respects permissions.

## Setup
### Inital installation
First, if you haven't already, add my repo:
> `[p]repo add toxic https://github.com/NeuroAssassin/Toxic-Cogs`

Next, install the cog:
> `[p]cog install toxic dashboard`

Finally, load the cog:
> `[p]load dashboard`
****
> NOTE: If you have multiple bot's running the cog, you will have to change the port used by using the command `[p]dashboard settings port <port_number_here>`.  The default is 42356.
****
### Setup web server
#### Redirect URI
Head over [here](https://discordapp.com/developers/applications/) to the Discord Developer Console, and click on your bot's application.  Note that it **must be** the bot you are setting this up for.  Next, click on the OAuth2 tab and click "Add Redirect".  Then, put the appropriate link down based upon what you are planning to do and how you are hosting:
****
##### If you are hosting on a VPS:
- http://ip.add.re.ss:42356/useCode (make sure to replace "ip.add.re.ss" with your VPS's IP address).
##### If you are hosting on a local computer:
- http://localhost:42356/useCode (if you aren't planning on allowing other people to use it)
- http://loc.al.ip.address:42356/useCode (also if you aren't planning on other people using it, but note that you must replace "loc.al.ip.address" with the one found in `ipconfig` in the command prompt, under IPv4).
- http://ip.add.re.ss:42356/useCode (if you are planning on making it public.  Note that this requires port forwarding set up, and the "ip.add.re.ss" must be replaced with the IP you see when you look up "what is my ip address").
****
Next, copy the redirect URI you just put into the field, and head over to the dashboard.  Type the following, replacing `<redirect>` with your redirect.
> `[p]dashboard settings redirect <redirect>`
#### Client Secret
Head over [here](https://discordapp.com/developers/applications/) to the DIscord Developer Console, and click on your bot's application.  Just like with the Redirect URI, this must be the same bot.  Next, head over to the right of the page and click on "Copy" under the Client Secret, NOT the Client ID.  Finally, head over to Discord and type the following command, replacing `<secret>` with your client secret:
> `[p]dashboard settings secret <secret>`

After that, you should be good to go!  In your web browser, open the link you put into the redirect URI earlier (minus the `/useCode`) and it should show you the welcome page.  Enjoy!
****
## Configuration and Other Details
### Logging errors
The dashboard comes with a couple things to configure.  For example, one of them is to log errors.  This allows for the bot to catch command errors and put them on the web dashboard for you to look at.  In order to enable, just type the following command:
`[p]dashboard settings logerrors True`
### Permissions
In order to make sure all permissions are respected, Discord OAuth is used for authentication for the dashboard.  This helps make sure that random users don't end up using the `[p]serverlock` command in the dashboard.  Permissions are judged based upon whether they are bot owner, guild owner, administrator, moderator or a normal user (in that order).  If not, the respective button will be greyed out, or they will receive a popup saying they aren't allowed to perform that operation.
### Contact
If you have any questions, issues or suggestions, feel free to stop by my server and tell me about them:
[![Discord server](https://discordapp.com/api/guilds/540613833237069836/embed.png?style=banner3)](https://discord.gg/vQZTdB9)