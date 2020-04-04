#!/usr/bin/python3

### environment variables 

eHash = {
    'initPrompt': '\$', ### the prompt your shell uses.  
    'opTool': './op', ### path to the 1password cli tool binary
    'url': 'NULL', ### 1password sign in address 
    'email': 'NULL', ### email address used to sign into 1password
    'key': 'NULL', ### 1 password secret key
}

badHabits = 'bad_habits.json'

timeOut = 20 

##################################

import json, getpass, subprocess, pexpect, os, time, re, sys
#from pprint import pprint

def logoutOption(S, ourPrompt):
    option = input('press enter to continue or q to quit... ')
    if option == 'q':
        signOut(S, ourPrompt)
        return(1)
    else:
        return(0)

def signOut(S, ourPrompt):
    S.sendline(eHash['opTool'] + ' signout')
    time.sleep(2)
    S.expect(ourPrompt)
    #print(S.before.decode())
    #print(S.after.decode())

def userLoop(deRail):
    if deRail == 1:
        ### login routine
        print('Signing into 1password...')
        S = pexpect.spawn('bash')
        S.expect(eHash['initPrompt'])
        ourPrompt = S.before.decode().split()[0]

        S.sendline(eHash['opTool'] + ' signin ' + eHash['url'] + ' ' + eHash['email'] + ' ' + eHash['key'])
        S.expect('at ' + eHash['url'].split('//')[1] + ':')

        S.sendline(eHash['ourPass'])
        S.expect('session token')

        tokenText = S.before.decode()

        tokenList = tokenText.splitlines()
        for l in tokenList:
            if 'OP_SESSION' in l:
                sessionToken = l

        S.sendline(sessionToken)
        S.expect('\$')

        print('Requesting list of items...')
        S.sendline(eHash['opTool'] + ' list items')
        time.sleep(1)
        S.expect(ourPrompt)
        while True:
            if 'OP_SESSION' in S.before.decode():
                S.sendline('\n')
                S.expect(ourPrompt)
                print('waiting for 1password items...')
                time.sleep(.5)
            else:
                break

        rawItems = S.before.decode().rstrip()
        rawSearch = re.search(r'.+op list items(\r\n)+(.+)', rawItems, re.DOTALL)
        itemList = json.loads(rawSearch.group(2), strict=False)
        #pprint(itemList)
        
        deRail = 0
########################################
    ### main routine
    while True:
        searchHash = {}
        searchTerm = input('\nEnter search term: ')
        ourCounter = 0
        for i in itemList:
            ourCounter += 1
            if searchTerm.lower() in i['overview']['title'].lower():
                searchHash[ourCounter] = {}
                searchHash[ourCounter]['title'] = i['overview']['title']
                searchHash[ourCounter]['ainfo'] = i['overview']['ainfo']
                searchHash[ourCounter]['uuid'] = i['uuid']
        if searchHash != {}:
            for i in searchHash:
                print(str(i) + ' - ' + searchHash[i]['title'])
            while True:
                accountSelect = input('\nEnter the number next to the desired account or s to search again or q to quit: ')
                try: 
                    if accountSelect == 's' or accountSelect == 'q' or int(accountSelect) in searchHash:
                        break
                except:
                    print(sys.exc_info())
                    pass
            if accountSelect == 'q':
                signOut(S, ourPrompt)
                #break
                sys.exit()
            if accountSelect != 's':
                print('looking up: ' + searchHash[int(accountSelect)]['title'] + '\n')
                
                S.sendline(eHash['opTool'] + ' get item ' + searchHash[int(accountSelect)]['uuid'])
                time.sleep(1)
                S.expect(ourPrompt)
                ourWait = 0
                while True:
                    ourWait += 1
                    if ourWait >= timeOut:
                        print('Session timeout... restarting routine...')
                        signOut(S, ourPrompt)
                        S.close()
                        deRail = 1
                        break
                    elif 'uuid' not in S.before.decode():
                        print('waiting for account details...')
                        S.sendline('\n')
                        time.sleep(.5)
                        S.expect(ourPrompt)
                    else:
                        break
                if deRail == 1:
                    break
                details = S.before.decode().rstrip()
                rawSearch = re.search(r'.+op.+(\r\n)+(.+)', details, re.DOTALL)
                detailsHash = json.loads(rawSearch.group(2), strict=False)
                #pprint(detailsHash)
                print()
                ### usual case
                if 'fields' in detailsHash['details']:
                    for i in detailsHash['details']['fields']:
                        if 'designation' in i:
                            if i['designation'] == 'password':
                                print('password: ' + i['value'])
                            elif i['designation'] == 'username':
                                print('username: ' + i['value'])
                ### server type
                elif 'sections' in detailsHash['details']:
                    for i in detailsHash['details']['sections']:
                        if 'fields' in i:
                            for d in i['fields']:
                                if 'n' in d and d['n'] == 'username':
                                    print('username: ' + d['v'])
                                elif 'n' in d and d['n'] == 'password':
                                    print('password: ' + d['v'])
                else:
                    print('This account type has not been accounted for...') 
                if 'sections' in detailsHash['details']:
                    for s in detailsHash['details']['sections']:
                        if 'fields' in s:
                            for f in s['fields']:
                                if 'n' in f:
                                    if 'TOTP' in f['n']:
                                        while True:
                                            otpOption = input('get otp? (y/n): ')
                                            if otpOption == 'n':
                                                break
                                            elif otpOption == 'y':
                                                S.sendline(eHash['opTool'] + ' get totp ' + searchHash[int(accountSelect)]['uuid'])
                                                time.sleep(1)
                                                S.expect(ourPrompt)
                                                ourWait = 0
                                                while True:
                                                    ourWait += 1
                                                    if ourWait >= timeOut:
                                                        print('Session timeout... restarting routine...')
                                                        signOut(S, ourPrompt)
                                                        S.close()
                                                        deRail = 1
                                                        break
                                                    elif 'op get totp' not in S.before.decode():
                                                        print('waiting for otp...')
                                                        S.sendline('\n')
                                                        time.sleep(.5)
                                                        S.expect(ourPrompt)
                                                    else:
                                                        break
                                                if deRail == 1:
                                                    break
                                                otpReturn = S.before.decode().rstrip()
                                                otpSearch = re.match(r'.+op get totp.+(\r\n)+(.+)', otpReturn)
                                                
                                                print('\notp:  ' + otpSearch.group(2))
                if deRail == 1:
                    break
                ourOption = logoutOption(S, ourPrompt)
                if ourOption == 1:
                    #break
                    sys.exit()

#################################################
### This is run time
#################################################

if os.path.exists(badHabits):
    try:
        with open(badHabits) as ourJson:
            eHash = json.load(ourJson)
    except:
        pass
else:
    if eHash['url'] == 'NULL':
        eHash['url'] = input('Enter your sign-in address (url): ')
    if eHash['email'] == 'NULL':
        eHash['email'] = input('Enter your email address: ')
    if eHash['key'] == 'NULL':
        eHash['key'] = getpass.getpass(prompt='Enter your Secret Key: ')
    eHash['ourPass'] = getpass.getpass(prompt='Enter your Master Password: ')


while True:
    userLoop(1)
