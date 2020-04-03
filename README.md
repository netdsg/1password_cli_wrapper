# 1password_cli_wrapper
A wrapper for the 1password cli tool

Currently only returns username, password and OTP.  Let me know what ought to added!  

At the top of the script set these variables to suit your needs.
```
eHash = {
    'initPrompt': '\$', ### the prompt your shell uses.  
    'opTool': './op', ### path to the 1password cli tool binary
    'url': 'NULL', ### 1password sign in address 
    'email': 'NULL', ### email address used to sign into 1password
    'key': 'NULL', ### 1 password secret key
}
```
