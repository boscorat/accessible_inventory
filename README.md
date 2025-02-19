# ACCESSIBLE INVENTORY
    #### Video Demo:  https://youtu.be/5RTerzGCaNw
    #### Description:  Accessible inventory tracking, designed to be simple to use for those without database or spreadsheet experience

Accessible Inventory is a simple application to help you log and manage your inventory. You could use accessible inventory to keep track of items within a home you're renting out, or in your loft, or even in your different cupboards. It's incredibly flexible!

All the functionality is accessible through simple commands, and requires no experience of databases or spreadsheets.  Simply ask accessible inventory to 'add 2 yellow chairs to the kitchen' or 'remove 1 small table from the lounge', and your inventory will be updated.

You can also remove items from your inventory with 'remove 2 yellow chairs from the kitchen', and show your current inventory by location or location with 'show lounge' or 'show yellow chairs'.  If you want to see all items by locations you can use 'show all locations' or all locations by item with 'show all items'.

Have a play around and see how you get on.

## Installation

Clone the repository or download the project.py file to your system, and use pip to install the single dependency:

```bash
pip install inflex
```
and then run:

```bash
python project.py
```

## Usage

###### When first running you will be greeted with the following introductory information:
```bash
Welcome to the Accessible Inventory Application
-----------------------------------------------

Help - entering instructions

Adding or Removing inventory items:
your instruction should be in the format of add|remove qty item(s) to|from location
e.g. 'add 3 red chairs to the dining room' or 'remove 1 desk from the study'

Showing inventory of an item or contents of a location:
your instruction should be in the format of show item|location
e.g. 'show red tables' or 'show small chair' or 'show lounge'
or you can get a full report by item with 'show all items' or by location with 'show all locations'

Entering the instruction 'help' will show these instructions again

```
###### add your first inventory item at the instruction prompt:
```bash
What is your instruction? add 1 old red chair to the lounge
'Success! 1 old red chair added to lounge
```
You must include a quantity, as well as an item and a location.  If you miss something out you'll be prompted to make amendments. By giving your instruction 'help', you can see the guidance on entering instructions displayed at any point.

Items and locations can be as verbose as you like.  If you want to 'add 2 old smelly scruffy nasty dog blankets to the cold dark damp hallway', then that's fine!  it doesn't even matter if you then add another with 'add 1 smelly nasty scruffy old dog blanket to the damp cold dark hallway', as accessible inventory will ignore the order of the adjectives and recognise these as an additional item in the same location.

###### try adding a few more items:
```bash
What is your instruction? add 1 dining table to lounge
'Success! 1 dining table added to lounge'

What is your instruction? add 1 cd rack to the lounge
'Success! 1 cd rack added to lounge'

What is your instruction? add 2 yellow chairs to the lounge
'Success! 2 yellow chair added to lounge'

What is your instruction? add 1 yellow chair to the kitchen
'Success! 1 yellow chair added to kitchen'
```
Notice that accessible inventory doesn't care if you refer to 'lounge' or 'the lounge'.  It also doesn't mind if you use plurals or singulars.

###### now try showing the contents of the lounge:
```bash
What is your instruction? show lounge

lounge contents:
1 old red chair
1 dining table
1 cd rack
2 yellow chairs
```

###### you can also show the locations of the yellow chairs:

```
What is your instruction? show yellow chairs

yellow chair locations:
2 in the lounge
1 in the kitchen

```

###### or why not try showing all locations:
```
What is your instruction? show all locations

lounge contents:
1 old red chair
1 dining table
1 cd rack
2 yellow chairs

kitchen contents:
1 yellow chair
```
###### you can even have an item that's also a location - try this:
```
What is your instruction? add 3 beetles cds to the cd rack
Success! 3 beetles cd added to cd rack

What is your instruction? show cd rack

cd rack locations:
1 in the lounge


cd rack contents:
3 beetles cds
```
###### removing items is just as simple - try removing a yellow chair from the lounge where there are currently 2 located:
```
What is your instruction? remove 1 yellow chair from the lounge
Success! 1 yellow chair removed from lounge

What is your instruction? show lounge

lounge contents:
1 old red chair
1 dining table
1 cd rack
1 yellow chair
```

###### removing another yellow chair from the lounge will no longer show the yellow chairs in the lounge contents;
```
What is your instruction? remove 1 yellow chair from lounge
Success! 1 yellow chair removed from lounge

What is your instruction? show lounge

lounge contents:
1 old red chair
1 dining table
1 cd rack
```

## Current limitations

* Inventory is only stored for the current session as there is no persistent database storage currently configured
* When using an item as a location (e.g. cd rack), it is not possible to hold different contents for different cd racks.  If you have 3 cd racks, your list of cd's will be combined.
