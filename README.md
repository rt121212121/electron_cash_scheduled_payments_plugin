# Scheduled Payments - Electron Cash Plugin #

This is licensed under the MIT open source license.

## Installation ##

The 'scheduled_payments' folder is an [Electron Cash](https://electroncash.org/) plugin.  It needs to be made available to the copy of Electron Cash you plan to run it with.  The normal way to do this, is to copy the folder (that's the folder itself, not the files within it) into the `plugins` folder of that Electron Cash instance.

After the folder is in the correct place, start Electron Cash and open the Plugins window.  If you have installed the plugin correctly, you will see a disabled `Scheduled Payments` plugin.  Enable it, and a new tab `Scheduled Payments` will be added to your user interface.

## Security Warning ##

I, Roger Taylor (rt121212121), author of this plugin, affirm that there is no malicious code intentionally added by me to this plugin.  Unless you read through every line of the code provided, this is the best you are going to get at this time.  If you obtain this plugin from any other source than this github repository under my user name, then the safety of this plugin given my affirmation is worthless.

The reason this needs to be said, is that an enabled Electron Cash plugin has almost complete access and potential control over any wallets that are open.  If a malicious author wished to, they could make you think you were sending payments to one address and redirect them anywhere they wanted.  The possibilities are endless, due to the access a plugin has.

## Usage ##

Once you have the plugin installed and enabled, you may attempt to use it.

1. Select the `Scheduled Payments` tab.
2. Right click in the list window, and select the `New scheduled payment` item.
3. A dialog will appear that allows you to construct a scheduled payment.  It will estimate the next time that payment will be made, to help you visualise how your choice of when the payment will be made, will play out.  Select Create when you have filled out all the fields.
4. Wait until that new payment's next payment time passes.

## Known Issues ##

* The fake clock is not correctly hooked up to the payment scheduler.
* If you enter more than one address in the scheduled payment, who knows what will happen.  Don't do it.

