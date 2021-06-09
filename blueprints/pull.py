from flask import Blueprint, render_template, redirect, url_for, request, flash
from replit import db, database
from flask_login import current_user
import numpy as np

pullBP = Blueprint('pullBP', __name__)

#Generates a dictionary of owned characters
#Keys are the character IDs; values are the users that own them
def getListOwnedChars():
  characters = {}
  for pname, p in db['players'].items():
    for cind in p['roster']:
      characters[cind] = pname
  return characters

#Function to randomly select a characters
#Takes in a banner name as an argument, which effects rates
def pickChar(banner_name=None):
  #Gets the banner info
  if banner_name is None:
    banner = db['banners']['base']
  else:
    banner = db['banners'][banner_name]

  #Gets a list of all owned characters
  owned_chars = getListOwnedChars().keys()
  
  #Gets a list of characters filtering out the characters already owned
  viable_characters = {k:v for k,v in db['characters'].items() if k not in owned_chars}
  if viable_characters == {}:
    print('There are no characters at all')
    return None

  #Gets the rates for each banner
  rarities = banner['rates']
  if rarities is None:
    rarities = db['banners']['base']['rates']

  #Checks if a rarity has no valid characters to select
  valid_rarities = {
    r : 
    len(list(filter(
      lambda x: x['rarity']==int(r),
      viable_characters.values()
    )))>0
    for r in rarities.keys()
  }

  #Selects a rarity
  r_weights = [(r, w if valid_rarities[r] else 0) for r, w in rarities.items()]
  sum_weights = sum(map(lambda x: x[1], r_weights))
  r_weights  = [(r,float(w)/sum_weights) for r,w in r_weights]
  rarity_picked = int(np.random.choice(list(map(lambda x: x[0], r_weights)), p=list(map(lambda x: x[1], r_weights))))

  #Filters for selected rarity
  viable_characters = {k:v for k,v in viable_characters.items() if v['rarity']==rarity_picked}
  if viable_characters == {}:
    print('There are no characters within this rarity')
    return None
  
  #Picks character based on weighting function
  weight_function = eval(banner['weights'])
  print(weight_function)
  c_weights = [weight_function(c) for cid,c in viable_characters.items()]
  c_weights = [w/sum(c_weights) for w in c_weights]

  return np.random.choice(list(viable_characters.keys()), p=c_weights)

#Page with all the banners
@pullBP.route('/banners', methods=['GET','POST'])
def banners():  
  if request.method == 'POST':
    #Gets the info about the player and the button press
    player = db['players'][current_user.id]
    button = request.form.get('submit_button')

    #Checks if the button press was a pull
    if button.split('-')[0] == 'pull':
      banner_name = button.split('-')[1]
      cost = db['banners'][banner_name]['cost']

      #Checks if the player has enough coins
      if player['coins']-cost < 0:
        flash("You don't have enough coins.", category='error')

      else:

        #You don't a full roster
        if player['max_roster'] > len(player['roster']):
          new_char = pickChar(banner_name)
          db['players'][current_user.id]['roster'].append(new_char)

        #You do have a full roster
        else:
          new_char = pickChar(banner_name)
          db['players'][current_user.id]['pulled_character'] = new_char

        #Deducting the cost of the banner
        db['players'][current_user.id]['coins'] -= cost

        #Returns a page to show the user thier pull
        return render_template('pull/pulled.html', user = current_user, character = database.to_primitive(db['characters'][new_char]), chr_ind = new_char)

    #Checks if the button was a character removal
    elif button == 'remove':
      #Gets the character that's being removed
      removing = request.form.get('characterRemoving')
      if removing is not None:
        removing = removing.split('-')[1]
        #If the character selected the one that was just pulled
        if removing == 'pulled':
          db['players'][current_user.id]['pulled_character'] = None
        #If the character selected was already in thier roster
        else:
          removing = int(removing)
          db['players'][current_user.id]['roster'].pop(removing)
          db['players'][current_user.id]['roster'].append(player['pulled_character'])
          db['players'][current_user.id]['pulled_character'] = None



  player = db['players'][current_user.id]
  

  char_ids = database.to_primitive(player['roster']) 
  characters = [(str(ri), db['characters'][ci]) for ri,ci in enumerate(char_ids)]
  coins=player['coins']

  can_pull = player['pulled_character'] is None
  if can_pull:
    return render_template('pull/banners.html', user = current_user, coins=coins, coinstr = f"Pull: {coins}->{coins-1}", banners = db['banners'])
  else:
    pulled_char = (player['pulled_character'], db['characters'][player['pulled_character']])
    return render_template('pull/already_pulled.html', user = current_user, characters=characters, pulled_char = pulled_char)