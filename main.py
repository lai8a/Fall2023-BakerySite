# Team 3's Python driver
# This is the main driver for the project; hosts all methods, calls to database, as well as functionally runs the website.

from flask import Flask as fl
from flask import url_for, request, render_template, redirect, session, flash
import mysql.connector
import re
import random
import time as t
from datetime import date
from mailjet_rest import Client

# Initialize FLASK
app = fl(__name__, static_url_path='/static')
app.secret_key = "Team3Project"

# Mailjet API and Secret Key
api_key = 'b3d9180a7775b746916f1d9660cc35e9'
api_secret = '619a4964a6c2b83e0c543aa8acdc6414'
mailjet = Client(auth=(api_key, api_secret), version='v3.1')

# Database connection functions
def connectdb():
    try:
        mydb = mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = "mysql",
            database = "bakery"
        )
        print("Connected!")
        return mydb
    except:
        print("Connection failed, uh oh!")


def disconnectdb(mydb):
    mydb.close()


def updateNavBar(session):
    employee = session["employee"]
    loggedin = session["loggedin"]
    return employee, loggedin

@app.route("/")
def homepage():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)
    
    return render_template("index.html", employee=employee, loggedin=loggedin)

@app.route("/order", methods=["GET", "POST"])
def order():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)
    
    msg = ""
    # TODO: Test functionality
    if request.method == "POST" and "item" in request.form and "flavor" in request.form and "size" in request.form and "quantity" in request.form and "decorRequests" in request.form and "day" in request.form and "pickup" in request.form:
        items = request.form.getlist("item")
        flavors = request.form.getlist("flavor")
        sizes = request.form.getlist("size")
        quantities = request.form.getlist("quantity")
        requests = request.form.getlist("decorRequests")
        date = request.form["day"]
        time = request.form["pickup"]
        placed_time = t.localtime()
        timeString = t.strftime("%H:%M", placed_time)
        orderConfirmation = 1 + (random.random() * 125478) #Such a large number that we can't possibly have repeats
        mydb = connectdb()
        cursor = mydb.cursor()
        if session["loggedin"] == True:
            cursor.execute("SELECT * FROM Account WHERE Email = %s",[(session["email"])])
            account = cursor.fetchone()
            cursor.execute("INSERT INTO orders (ConfirmationNumber, OrderPlacedTime, OrderDate, OrderPickupTime, CustomerFirstName, CustomerLastName, CustomerEmail, CustomerPhone) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", (str(orderConfirmation), timeString, date, time, account[1], account[2], account[5], account[4]))
            for i in range(len(items)):
                cursor.execute("INSERT INTO OrderDetails (ConfirmationNumber, OrderCategory, Size, Flavor, Quantity, DecorRequests) VALUES(%s, %s, %s, %s, %s, %s)", (str(orderConfirmation), items[i], sizes[i], flavors[i], quantities[i], requests[i]))
        else:
            msg = "You must be logged in to order! Please make an account and try again!"
            flash(msg, category="danger")
            redirect(url_for("login"))
        mydb.commit()
        disconnectdb(mydb)
        msg = "Order Confirmation Number: " + str(orderConfirmation)
        flash(msg, category="success")
    elif request.method == "POST":
        msg = "Sorry, something went wrong! Try reloading and ordering again!"
        flash(msg, category="danger")

    return render_template("order.html", msg=msg, employee=employee, loggedin=loggedin)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)
    
    msg = ""
    if request.method == "POST" and "date" in request.form and "time" in request.form and "phone" in request.form and "email" in request.form and "question" in request.form:
        date = request.form["date"]
        time = request.form["time"]
        phone = request.form["phone"]
        email = request.form["email"]
        question = request.form["question"]
        mydb = connectdb()
        cursor = mydb.cursor()
        command = "INSERT INTO Contact (ContactDate, ContactTime, ContactPhone, ContactEmail, ContactQuestion) VALUES (%s, %s, %s, %s, %s)"
        values = (date, time, phone, email, question)
        cursor.execute(command, values)
        mydb.commit()
        # Testing below
        print(cursor.rowcount, " record inserted")
        disconnectdb(mydb)
        msg = "Form received! You may now exit this page."
        flash(msg, category="success")
    elif request.method == "POST":
        msg = "There was an error handling your request, please try again!"
        flash(msg, category="danger")
        # Testing below
        print(request.form, " List of all the data sent")

    return render_template("contact.html", msg=msg, employee=employee, loggedin=loggedin)

@app.route("/replyContact", methods=["GET", "POST"])
def replyContact():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    if 'employee' in session and session["employee"] != 1 or 'employee' not in session:
        print("You are not allowed to access this page!")
        return redirect(url_for("homepage"))
    
    msg = ""

    try: 
        mydb = connectdb()
        cursor = mydb.cursor()

        cursor.execute('SELECT * from Contact')
        contact = cursor.fetchall()
    except:
        print("An error has occurred while displaying the contact table!")

    if request.method == "POST" and request.form["replyConfirm"] == "1":
        print(request.form)
        contactID = request.form["contactID"]
        replyMsg = request.form["replyMsg"]
        cursor.execute("SELECT * FROM Contact WHERE ContactID = %s", [(contactID)])
        userContact = cursor.fetchone()
        print(userContact) # TESTING
        if userContact:
            contacteeName = userContact[4].split('@')[0]

            data = {
            'Messages': [
                    {
                        "From": {
                            "Email": "meil@go.stockton.edu",
                            "Name": "L&S Bakery Support Team"
                        },
                        "To": [
                            {
                                "Email": userContact[4],
                                "Name": contacteeName
                            }
                        ],
                        "TemplateID": 5379608,
                        "TemplateLanguage": True,
                        "Subject": "L&S Contact Reply to " + repr(contacteeName),
                        "Variables": {
                            "contactQuestion": userContact[5],
                            "contacteeName": contacteeName,
                            "replyContactMsg": replyMsg,
                            "contactID": userContact[0]
                        }
                    }
                ]
            }

            print(data)  # TESTING
            result = mailjet.send.create(data=data) # TESTING
            print (result.status_code) # TESTING
            print (result.json()) # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST":
        msg = "Please fill out the information before submitting!"
        flash(msg, category="danger")

    disconnectdb(mydb)

    return render_template("replyContact.html", msg=msg, contact=contact, employee=employee, loggedin=loggedin)

@app.route("/deleteContact", methods=["GET", "POST"])
def deleteContact():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    if 'employee' in session and session["employee"] != 1 or 'employee' not in session:
        print("You are not allowed to access this page!")
        return redirect(url_for("homepage"))
    
    msg = ""

    try: 
        mydb = connectdb()
        cursor = mydb.cursor()

        cursor.execute('SELECT * from Contact')
        contact = cursor.fetchall()
    except:
        print("An error has occurred while displaying the contact table!")

    if request.method == "POST" and request.form["replyConfirm"] == "1":
        print(request.form)
        contactID = request.form["contactID"]
        cursor.execute("SELECT * FROM Contact WHERE ContactID = %s", [(contactID)])
        userContact = cursor.fetchone()
        print(userContact) # TESTING
        if userContact:
            cursor.execute("DELETE from Contact WHERE ContactID = %s", [(contactID)])
            mydb.commit()
            print(cursor.rowcount, " record deleted!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST":
        msg = "Please fill out the information before submitting!"
        flash(msg, category="danger")

    disconnectdb(mydb)

    return render_template("deleteContact.html", msg=msg, contact=contact, employee=employee, loggedin=loggedin)

@app.route("/adminPage")
def adminPage():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    if 'employee' in session and session["employee"] == 1:
        return render_template("adminPage.html", employee=employee, loggedin=loggedin)
    else:
        print("You are not allowed to access this page!")
        return redirect(url_for("homepage"))
        

@app.route("/menu")
def menu():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)
    
    try:
        mydb = connectdb()
        cursor = mydb.cursor()

        cursor.execute('SELECT * FROM minidesserts')
        miniMenu = cursor.fetchall()

        cursor.execute('SELECT * FROM desserttray')
        trays = cursor.fetchall()
    
        cursor.execute('SELECT * FROM pieandcheesecake')
        piecheese = cursor.fetchall()

        cursor.execute('SELECT * FROM cupcake')
        cupcake = cursor.fetchall()

        cursor.execute('SELECT * FROM dietary')
        dietary = cursor.fetchall()

        cursor.execute('SELECT * FROM signatureflavorcake')
        sf = cursor.fetchall()

        cursor.execute('SELECT * FROM cake')
        cake = cursor.fetchall()

        disconnectdb(mydb)
        return render_template("menu.html", miniMenu=miniMenu, trays=trays, piecheese=piecheese, cupcake=cupcake, dietary=dietary, sf=sf, cake=cake, employee=employee, loggedin=loggedin)
    except:
        print("An error has occurred while displaying the menu!")

# Admin Menu Functions below
# ADDING TO MENU
@app.route("/addMenu", methods=["GET", "POST"])
def addMenu():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    if 'employee' in session and session["employee"] != 1 or 'employee' not in session:
        print("You are not allowed to access this page!")
        return redirect(url_for("homepage"))

    msg = ""
    if request.method == "POST" and request.form["menuID"] == "1":
        menuID = request.form["menuID"]
        categoryName = request.form["categoryName"]
        dessertName = request.form["dessertName"]
        dessertPrice = request.form["dessertPrice"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO MiniDesserts (MenuID, CategoryName, DessertName, DessertPrice) VALUES (%s, %s, %s, %s)", (menuID, categoryName, dessertName, dessertPrice))
        mydb.commit()
        print(cursor.rowcount, " record inserted!") # TESTING
        disconnectdb(mydb)
        msg = "Form received! You may now exit this page."
        flash(msg, category="success")
    elif request.method == "POST" and request.form["menuID"] == "2":
        menuID = request.form["menuID"]
        categoryName = request.form["categoryName"]
        sizeName = request.form["sizeName"]
        sizePrice = request.form["sizePrice"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO DessertTray (MenuID, CategoryName, SizeName, SizePrice) VALUES (%s, %s, %s, %s)", (menuID, categoryName, sizeName, sizePrice))
        mydb.commit()
        print(cursor.rowcount, " record inserted!") # TESTING
        disconnectdb(mydb)
        msg = "Form received! You may now exit this page."
        flash(msg, category="success")
    elif request.method == "POST" and request.form["menuID"] == "3":
        menuID = request.form["menuID"]
        categoryName = request.form["categoryName"]
        PCName = request.form["PCName"]
        PCPrice = request.form["PCPrice"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO PieAndCheesecake (MenuID, CategoryName, PCName, PCPrice) VALUES (%s, %s, %s, %s)", (menuID, categoryName, PCName, PCPrice))
        mydb.commit()
        print(cursor.rowcount, " record inserted!") # TESTING
        disconnectdb(mydb)
        msg = "Form received! You may now exit this page."
        flash(msg, category="success")
    elif request.method == "POST" and request.form["menuID"] == "4":
        menuID = request.form["menuID"]
        sizeName = request.form["sizeName"]
        sizeDescription = request.form["sizeDescription"]
        cupcakePrice = request.form["cupcakePrice"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO Cupcake (MenuID, SizeName, SizeDescription, CupcakePrice) VALUES (%s, %s, %s, %s)", (menuID, sizeName, sizeDescription, cupcakePrice))
        mydb.commit()
        print(cursor.rowcount, " record inserted!") # TESTING
        disconnectdb(mydb)
        msg = "Form received! You may now exit this page."
        flash(msg, category="success")
    elif request.method == "POST" and request.form["menuID"] == "5":
        menuID = request.form["menuID"]
        categoryName = request.form["categoryName"]
        cakeSize = request.form["cakeSize"]
        dietaryPrice = request.form["dietaryPrice"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO Dietary (MenuID, CategoryName, CakeSize, DietaryPrice) VALUES (%s, %s, %s, %s)", (menuID, categoryName, cakeSize, dietaryPrice))
        mydb.commit()
        print(cursor.rowcount, " record inserted!") # TESTING
        disconnectdb(mydb)
        msg = "Form received! You may now exit this page."
        flash(msg, category="success")
    elif request.method == "POST" and request.form["menuID"] == "6":
        menuID = request.form["menuID"]
        categoryName = request.form["categoryName"]
        cakeSize = request.form["cakeSize"]
        servings = request.form['servings']
        SFPrice = request.form["SFPrice"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO SignatureFlavorCake (MenuID, CategoryName, CakeSize, Servings, SFPrice) VALUES (%s, %s, %s, %s, %s)", (menuID, categoryName, cakeSize, servings, SFPrice))
        mydb.commit()
        print(cursor.rowcount, " record inserted!") # TESTING
        disconnectdb(mydb)
        msg = "Form received! You may now exit this page."
        flash(msg, category="success")
    elif request.method == "POST" and request.form["menuID"] == "7":
        menuID = request.form["menuID"]
        cakeSize = request.form["cakeSize"]
        servings = request.form['servings']
        cakePrice = request.form['cakePrice']
        cakeEnhancement = request.form['cakeEnhancement']
        fillingEnhancement = request.form['fillingEnhancement']
        frostingEnhancement = request.form['frostingEnhancement']
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("INSERT INTO Cake (MenuID, CakeSize, Servings, CakePrice, CakeEnhancement, FillingEnhancement, FrostingEnhancement) VALUES (%s, %s, %s, %s, %s, %s, %s)", (menuID, cakeSize, servings, cakePrice, cakeEnhancement, fillingEnhancement, frostingEnhancement))
        mydb.commit()
        print(cursor.rowcount, " record inserted!") # TESTING
        disconnectdb(mydb)
        msg = "Form received! You may now exit this page."
        flash(msg, category="success")
    elif request.method == "POST":
        msg = "There was an error handling your request, please try again!"
        flash(msg, category="danger")
        # Testing below
        print(request.form, " List of all the data sent")

    return render_template("addMenu.html", msg=msg, employee=employee, loggedin=loggedin)

# EDITING THE MENU
@app.route("/editMenu", methods=["GET", "POST"])
def editMenu():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    if 'employee' in session and session["employee"] != 1 or 'employee' not in session:
        print("You are not allowed to access this page!")
        return redirect(url_for("homepage"))
    
    msg = ""

    try:
        mydb = connectdb()
        cursor = mydb.cursor()

        cursor.execute('SELECT * FROM minidesserts')
        miniMenu = cursor.fetchall()

        cursor.execute('SELECT * FROM desserttray')
        trays = cursor.fetchall()
        
        cursor.execute('SELECT * FROM pieandcheesecake')
        piecheese = cursor.fetchall()

        cursor.execute('SELECT * FROM cupcake')
        cupcake = cursor.fetchall()

        cursor.execute('SELECT * FROM dietary')
        dietary = cursor.fetchall()

        cursor.execute('SELECT * FROM signatureflavorcake')
        sf = cursor.fetchall()

        cursor.execute('SELECT * FROM cake')
        cake = cursor.fetchall()
    except:
        print("An error has occurred while displaying the table in editMenu!")

    if request.method == "POST" and request.form["menuID"] == "1":
        miniDessertsID = request.form["miniDessertsID"]
        categoryName = request.form["categoryName"]
        dessertName = request.form["dessertName"]
        dessertPrice = request.form["dessertPrice"]
        cursor.execute("SELECT * FROM MiniDesserts WHERE MiniDessertsID = %s", [(miniDessertsID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("UPDATE MiniDesserts SET CategoryName = %s, DessertName = %s, DessertPrice = %s WHERE MiniDessertsID = %s", (categoryName, dessertName, dessertPrice, miniDessertsID))
            mydb.commit()
            print(cursor.rowcount, " record updated!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "2":
        dessertTrayID = request.form["dessertTrayID"]
        categoryName = request.form["categoryName"]
        sizeName = request.form["sizeName"]
        sizePrice = request.form["sizePrice"]
        cursor.execute("SELECT * FROM DessertTray WHERE DessertTrayID = %s", [(dessertTrayID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("UPDATE DessertTray SET CategoryName = %s, SizeName = %s, SizePrice = %s WHERE DessertTrayID = %s", (categoryName, sizeName, sizePrice, dessertTrayID))
            mydb.commit()
            print(cursor.rowcount, " record updated!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "3":
        PCID = request.form["PCID"]
        categoryName = request.form["categoryName"]
        PCName = request.form["PCName"]
        PCPrice = request.form["PCPrice"]
        cursor.execute("SELECT * FROM PieAndCheesecake WHERE PCID = %s", [(PCID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("UPDATE PieAndCheesecake SET CategoryName = %s, PCName = %s, PCPrice = %s WHERE PCID = %s", (categoryName, PCName, PCPrice, PCID))
            mydb.commit()
            print(cursor.rowcount, " record updated!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "4":
        cupcakeID = request.form["cupcakeID"]
        sizeName = request.form["sizeName"]
        sizeDescription = request.form["sizeDescription"]
        cupcakePrice = request.form["cupcakePrice"]
        cursor.execute("SELECT * FROM Cupcake WHERE CupcakeID = %s", [(cupcakeID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("UPDATE Cupcake SET SizeName = %s, SizeDescription = %s, CupcakePrice = %s WHERE CupcakeID = %s", (sizeName, sizeDescription, cupcakePrice, cupcakeID))
            mydb.commit()
            print(cursor.rowcount, " record updated!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "5":
        dietaryID = request.form["dietaryID"]
        categoryName = request.form["categoryName"]
        cakeSize = request.form["cakeSize"]
        dietaryPrice = request.form["dietaryPrice"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM Dietary WHERE dietaryID = %s", [(dietaryID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("UPDATE Dietary SET CategoryName = %s, CakeSize = %s, DietaryPrice = %s WHERE dietaryID = %s", (categoryName, cakeSize, dietaryPrice, dietaryID))
            mydb.commit()
            print(cursor.rowcount, " record updated!") # TESTING
            disconnectdb(mydb)
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "6":
        SFID = request.form['SFID']
        categoryName = request.form["categoryName"]
        cakeSize = request.form["cakeSize"]
        servings = request.form['servings']
        SFPrice = request.form["SFPrice"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM signatureflavorcake WHERE SFID = %s", [(SFID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("UPDATE signatureflavorcake SET CategoryName = %s, CakeSize = %s, servings = %s, SFPrice = %s WHERE SFID = %s", (categoryName, cakeSize, servings, SFPrice, SFID))
            mydb.commit()
            print(cursor.rowcount, " record updated!") # TESTING
            disconnectdb(mydb)
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "7":
        cakeID = request.form['cakeID']
        cakeSize = request.form["cakeSize"]
        servings = request.form['servings']
        cakePrice = request.form["cakePrice"]
        cakeEnhancement = request.form["cakeEnhancement"]
        fillingEnhancement = request.form["fillingEnhancement"]
        frostingEnhancement = request.form["frostingEnhancement"]
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM cake WHERE cakeID = %s", [(cakeID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("UPDATE cake SET CakeSize = %s, servings = %s, cakePrice = %s, cakeEnhancement = %s, fillingEnhancement = %s, frostingEnhancement = %s WHERE cakeID = %s", (cakeSize, servings, cakePrice, cakeEnhancement, fillingEnhancement, frostingEnhancement, cakeID))
            mydb.commit()
            print(cursor.rowcount, " record updated!") # TESTING
            disconnectdb(mydb)
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST":
        msg = "There was an error handling your request, please try again!"
        flash(msg, category="danger")
        # Testing below
        print(request.form, " List of all the data sent")

    disconnectdb(mydb)

    return render_template("editMenu.html", msg=msg, miniMenu=miniMenu, trays=trays, piecheese=piecheese, cupcake=cupcake, dietary=dietary, sf=sf, cake=cake, employee=employee, loggedin=loggedin)

# DELETING FROM MENU
@app.route("/deleteMenu", methods=["GET", "POST"])
def deleteMenu():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    if 'employee' in session and session["employee"] != 1 or 'employee' not in session:
        print("You are not allowed to access this page!")
        return redirect(url_for("homepage"))
    
    msg = ""

    try:
        mydb = connectdb()
        cursor = mydb.cursor()

        cursor.execute('SELECT * FROM minidesserts')
        miniMenu = cursor.fetchall()

        cursor.execute('SELECT * FROM desserttray')
        trays = cursor.fetchall()
        
        cursor.execute('SELECT * FROM pieandcheesecake')
        piecheese = cursor.fetchall()

        cursor.execute('SELECT * FROM cupcake')
        cupcake = cursor.fetchall()

        cursor.execute('SELECT * FROM dietary')
        dietary = cursor.fetchall()

        cursor.execute('SELECT * FROM signatureflavorcake')
        sf = cursor.fetchall()

        cursor.execute('SELECT * FROM cake')
        cake = cursor.fetchall()
    except:
        print("An error has occurred while displaying the table in deleteMenu!")

    if request.method == "POST" and request.form["menuID"] == "1": 
        minidessertsID = request.form["miniDessertsID"]
        cursor.execute("SELECT * FROM minidesserts WHERE miniDessertsID = %s", [(minidessertsID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("DELETE from minidesserts WHERE miniDessertsID = %s", [(minidessertsID)])
            mydb.commit()
            print(cursor.rowcount, " record deleted!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "2":
        dessertTrayID = request.form["dessertTrayID"]
        cursor.execute("SELECT * FROM DessertTray WHERE DessertTrayID = %s", [(dessertTrayID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("DELETE from DessertTray WHERE DessertTrayID = %s", [(dessertTrayID)])
            mydb.commit()
            print(cursor.rowcount, " record deleted!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "3":
        PCID = request.form["PCID"]
        cursor.execute("SELECT * FROM PieAndCheesecake WHERE PCID = %s", [(PCID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("DELETE from PieAndCheesecake WHERE PCID = %s", [(PCID)])
            mydb.commit()
            print(cursor.rowcount, " record deleted!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "4":
        cupcakeID = request.form["cupcakeID"]
        cursor.execute("SELECT * FROM Cupcake WHERE CupcakeID = %s", [(cupcakeID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("DELETE from Cupcake WHERE CupcakeID = %s", [(cupcakeID)])
            mydb.commit()
            print(cursor.rowcount, " record deleted!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "5":
        dietaryID = request.form["dietaryID"]
        cursor.execute("SELECT * FROM dietary WHERE dietaryID = %s", [(dietaryID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("DELETE from dietary WHERE dietaryID = %s", [(dietaryID)])
            mydb.commit()
            print(cursor.rowcount, " record deleted!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "6":
        SFID = request.form["SFID"]
        cursor.execute("SELECT * FROM SignatureFlavorCake WHERE SFID = %s", [(SFID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("DELETE from SignatureFlavorCake WHERE SFID = %s", [(SFID)])
            mydb.commit()
            print(cursor.rowcount, " record deleted!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST" and request.form["menuID"] == "7":
        cakeID = request.form["cakeID"]
        cursor.execute("SELECT * FROM Cake WHERE cakeID = %s", [(cakeID)])
        item = cursor.fetchone()
        if item:
            cursor.execute("DELETE from Cake WHERE cakeID = %s", [(cakeID)])
            mydb.commit()
            print(cursor.rowcount, " record deleted!") # TESTING
            msg = "Form received! You may now exit this page."
            flash(msg, category="success")
        else:
            msg = "Sorry, the ID inputted was not found!"
            flash(msg, category="danger")
    elif request.method == "POST":
        msg = "There was an error handling your request, please try again!"
        flash(msg, category="danger")
        # Testing below
        print(request.form, " List of all the data sent")

    disconnectdb(mydb)

    return render_template("deleteMenu.html", msg=msg, miniMenu=miniMenu, trays=trays, piecheese=piecheese, cupcake=cupcake, dietary=dietary, sf=sf,cake=cake, employee=employee, loggedin=loggedin)

@app.route("/register", methods=["GET", "POST"])
def register():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    if "loggedin" in session and session["loggedin"] == True:
        return(redirect(url_for("profile")))
    
    msg = ""
    mydb = connectdb()
    cursor = mydb.cursor()

    #TODO: Suggestion: Confirm password field for form validation.
    if request.method == "POST" and "password" in request.form and "email" in request.form and "firstname" in request.form and "lastname" in request.form and "phone" in request.form:
        password = request.form["password"]
        email = request.form["email"]
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        phone = request.form["phone"]
        cursor.execute("SELECT * FROM ACCOUNT WHERE Email = %s", [(email)])
        account = cursor.fetchone()
        if account:
            msg = "Account already exists, login to your account!"
            flash(msg, category="danger")
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = "Invalid email! Try again!"
            flash(msg, category="danger")
        elif not password or not email:
            msg = "Incomplete form, please try again."
            flash(msg, category="danger")
        else:
            cursor.execute("INSERT INTO ACCOUNT (Firstname, Lastname, Password, Email, Phone) VALUES(%s, %s, %s, %s, %s)", (firstname, lastname, password, email, phone))
            mydb.commit()
            msg = "Successfully registered! You may now login!"
            flash(msg, category="success")
            disconnectdb(mydb)
            return redirect(url_for("login"))
    elif request.method == "POST":
        msg = "Please fill out the information before submitting!"
        flash(msg, category="danger")

    return render_template("register.html", msg = msg, employee=employee, loggedin=loggedin)

@app.route("/login", methods = ["GET", "POST"])
def login():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)
    
    msg = ""
    mydb = connectdb()
    cursor = mydb.cursor()
    if "loggedin" in session and session["loggedin"] == True:
        return(redirect(url_for("profile")))
    if request.method == "POST" and "email" in request.form and "password" in request.form:
        email = request.form["email"]
        password = request.form["password"]
        cursor.execute("SELECT * FROM ACCOUNT WHERE Email = %s AND Password = %s", (email, password))
        account = cursor.fetchone()
        if account and account[6] == 0:
            session["loggedin"] = True
            session["id"] = account[0]
            session["email"] = email
            session["employee"] = account[6]
            session['deleted'] = False
            msg = "Successfully logged in! You may now order!"
            flash(msg, category="success")
            disconnectdb(mydb)
            return redirect(url_for("profile"))
        elif account and account[6] == 1:
            session["loggedin"] = True
            session["id"] = account[0]
            session["email"] = email
            session["employee"] = account[6]
            session['deleted'] = False
            msg = "Successfully logged in! Redirecting to the admin page!"
            flash(msg, category="success")
            disconnectdb(mydb)
            return redirect(url_for("adminPage"))
        else:
            msg = "Incorrect login!"
            flash(msg, category="danger")

    return render_template("login.html", msg = msg, employee=employee, loggedin=loggedin)

@app.route("/logout")
def logout():
    #TODO: Allow logging out and removal of session data (non priority)

    if 'loggedin' in session and session["loggedin"] == True and session["deleted"] == False:
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('email', None)
        session.pop('employee', None)
        session.pop('deleted', None)
        msg = "You've been logged out!"
        print(msg)
        flash(msg, category="primary")
    elif 'loggedin' in session and session["loggedin"] == True and session["deleted"] == True:
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('email', None)
        session.pop('employee', None)
        session.pop('deleted', None)
        msg = "Sorry to see you go."
        print(msg)
        flash(msg, category="primary")
    else:
        msg = "You're not logged in!"
        print(msg)
        flash(msg, category="primary")

    return redirect(url_for('login'))

@app.route("/profile", methods = ["GET", "POST"])
def profile():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    #TODO: Test functionality
    mydb = connectdb()
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM Account WHERE Email = %s", ([session["email"]]))
    account = cursor.fetchone()
    print(account)
    #TODO: Fix bugs, people could set their emails to an already existing email (may have potential conflicts). Suggestion: User should confirm their old password before they are able to update the page.
    if request.method == "POST" and request.form["profile-form"] == "1" and "deleteAccount" not in request.form:
        print(request.form)
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        sessionEmail = session["email"]
        cursor.execute("UPDATE account SET Firstname = %s, LastName = %s, Email = %s, Password=%s, Phone = %s WHERE Email = %s", (firstname, lastname, email, password, phone, sessionEmail))
        mydb.commit()
        session["email"] = request.form["email"]
        flash("Updated Profile Information!", category='success')
        print(firstname, lastname, email, phone, sessionEmail)
        disconnectdb(mydb)
    elif request.method == "POST" and "deleteAccount" in request.form:
        mydb = connectdb()
        cursor = mydb.cursor()
        cursor.execute("DELETE From account WHERE Email = %s", ([session["email"]]))
        mydb.commit()
        disconnectdb(mydb)
        session["deleted"] = True
        return redirect(url_for("logout"))
    return render_template("profile.html", account = account, employee=employee, loggedin=loggedin)

@app.route('/viewOrder')
def viewOrder():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    # Most recent Order
    #TODO: Test functionality, and account for all previous orders
    mydb = connectdb()
    cursor = mydb.cursor()
    orderInfo = {}
    try:
        cursor.execute("SELECT * FROM orders WHERE CustomerEmail = %s", ([session["email"]]))
        orders = cursor.fetchall()
        print(orders)
        for item in orders:
            cursor.execute("SELECT * FROM orderDetails WHERE ConfirmationNumber = %s", [item[1]])
            orderInfo[item[1]] = cursor.fetchall()
            print(orderInfo[item[1]])
    except:
        print("An error has occurred while displaying your orders!")
        flash("You have no recent orders!", category="danger")
        return redirect(url_for("profile"))
    finally:
        disconnectdb(mydb)
        return render_template("viewOrder.html", orders = orders, orderInfo = orderInfo, employee=employee, loggedin=loggedin)

@app.route("/viewTodaysOrders.html")
def viewTodaysOrders():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)

    if 'employee' in session and session["employee"] != 1 or 'employee' not in session:
        flash("You are not allowed to access this page!", category="danger")
        return redirect(url_for("index"))
    
    mydb = connectdb()
    cursor = mydb.cursor()
    orderInfo = {}
    try:
        today = str(date.today())
        cursor.execute("SELECT * FROM orders WHERE OrderDate = %s", [today])
        orders = cursor.fetchall()
        print(orders)
        for item in orders:
            cursor.execute("SELECT * FROM orderDetails WHERE ConfirmationNumber = %s", [item[1]])
            orderInfo[item[1]] = cursor.fetchall()
            print(orderInfo[item[1]])
    except:
        print("No daily orders! Redirecting to the admin page!")
        flash("No daily orders! Redirecting to the admin page!", category="danger")
        return redirect(url_for("adminPage"))
    finally:
        disconnectdb(mydb)
        return render_template("viewTodaysOrders.html", today = today, orders = orders, orderInfo = orderInfo, employee=employee, loggedin=loggedin)

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/galleryphotos")
def galleryphotos():
    employee = 0
    loggedin = False
    if 'loggedin' in session:
        employee, loggedin = updateNavBar(session)
    
    return render_template("galleryphotos.html", employee=employee, loggedin=loggedin)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))  # default port
    app.run(host='0.0.0.0', port=port)
