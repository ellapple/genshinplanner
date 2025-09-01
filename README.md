# Genshin Planner
## Watch the demo [here](https://youtu.be/enRZK2Se8C0)!
## Description
The Genshin Planner is a website designed to help keep you motivated and save for the characters you want, allowing users to view events running within a 7 month period, a to do list to keep track of your daily (or weekly) tasks, and a handy savings calculator that'll tell you how many primogems you can earn in a time you set.
## Files
### Structure
```
/project
│── static/
│ ├── favicon.ico       # Favicon for the website
│ └── styles.css        # Stylesheet
│
│── templates/
│ ├── calculated.html   # Results for calculations.html
│ ├── calculations.html # Calculates primogems
│ ├── calendar.html     # Calendar with events
│ ├── index.html        # Homepage
│ ├── layout.html       # Layout with navbar
│ ├── login.html        # Login
│ ├── register.html     # Registers accounts
│ ├── settings.html     # Settings and bug reports
│ └── todo.html         # To-do list
│
│── app.db              # SQLite Database
│── app.py              # Flask backend
│── README.md           # Documentation
│── requirements.txt    # Dependencies
```
### index.html
* Homepage
* Summarizes the current events, providing easy access to the remaining time for an event.
* Reminds you of your unfinished to do list tasks
### calendar.html
* Calendar for the 7 month period around today's date
* Records the past (and future, if known) events
* Directs you to the Fandom page for the event upon clicking it
### todo.html
* To-do list
* Helps keep you motivated and logging in everyday
* Allows the user to add tasks (provided they are logged in) and set a name, description, and how often they want it to repeat
* Allows the user to edit the tasks' descriptions and repeat intervals
* Allows the user to remove tasks
### calculations.html
* Primogem Calculator
* Calculates how many primogems can be earned based on factors such as:
  * Static sources (such as comissions and HoyoLab check-in)
  * Exploration (based on the three regions available currently, using exploration progress and estimation mode to ultimately come to a more-or-less accurate estimate)
  * Paid sources (Blessing of the Welkin Moon and Battlepass)
  * Endgame content (such as the Spiral Abyss and Stygian Onslaught)
  * Paimon's Bargains (using Starglitter and Stardust)
* All calculations have been modified to be the most accurate they can be
* Allows the user to switch between a primogem view and intertwined fate view
### calculated.html
* Displays the results of the primogem calculator
### settings.html
* Settings
* Handles logging out, deleting account, and changing username and password
* Allows the user to submit up to 5 bug reports per day, to prevent spamming
### login.html
* Login
* Allows the user to log in to an account
* Links to register.html if user does not have an account
### register.html
* Register
* Allows the user to create an account
* Links to login.html if the user already has an account
### layout.html
* Handles the consistent layout of elements between pages
* Gives users reminders to log in, if they have not already
* Provides a convenient navigation bar for users to use
## Design Choices
### Calendar
Deciding whether to load all the calendar pages at once or on user request was difficult. Whilst I didn't know how to implement it, loading all of it at once would make the user experience much better, and that is what I ultimately went with.
Another small choice I made with the calendar was with the buttons to go to the previous month and the next month. Originally, the buttons all had the words 'prev' and 'next', and instead of being disabled just disappeared once the months were no longer available. Having 'prev' and 'next' on all of the buttons felt a bit repetitive and also didn't end up feeling as good to navigate as having the month names, so I changed it. Additionally, having the button disappear when reaching the boundary with no explanation felt quite unintuitive for the user, so I tried changing it to 'Out of range'. In the end, I settled with the month name to maintain consistency.
### Primogem Calculator
The calculator was also a difficult part to decide how to design. While it was always a table, it was formatted quite differently from how it is now. All the sources were condensed in one table, and many things were nested. While this did work, it didn't look very good and felt janky to use and not like a calculator at all. Sectioning it out helped it to look much more reliable and easier for the user to see the user of it.
### Layout
The navbar was the thing I added to the project first. I iterated through several different types, before finally settling on Bootstrap's Underline design of it because it felt the most friendly of them, which was perfect for a project centered around calculating savings for a game.
