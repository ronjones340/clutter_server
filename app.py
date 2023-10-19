from flask import Flask, request,jsonify
from flask_socketio import SocketIO,emit
from flask_cors import CORS
from random import shuffle, randint
from uuid import uuid4
from infobip_channels.sms.channel import SMSChannel
from pymongo.mongo_client import MongoClient
# from pymongo import MongoClient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'AEF25993SACTFUWOPLMSFEWUHJAFQLP9873!'
app.config['MONGO_URI'] = "mongodb+srv://ronjones8417:Emmanu3l698@cluster0.alreawj.mongodb.net/?retryWrites=true&w=majority"
CORS(app,resources={r"/*":{"origins":"*"}})

client = MongoClient("mongodb+srv://ronjones8417:Emmanu3l698@cluster0.alreawj.mongodb.net/?retryWrites=true&w=majority",connect=False)
db = client['Clutter']

socketio = SocketIO(app,cors_allowed_origins="*")
# mongo = PyMongo(app)

API_KEY = "c419e63bfe1c78c294632dedba6bdcd0-052291eb-959b-47c2-b7f2-eb8a249d54b6"
OTP_URL = "w11qj8.api.infobip.com"

# print(client.list_database_names())


USER_COMM_DETAILS = {}
Picked_List = []
registered_users = {}
usernames = []
emails = []
GAMES = {}
GAME_PLAYERS = {}
Player_arrangement = {}
LoggedInPlayers = {"Total_online": 0}
Is_allowed = {"Value": True}

TOURNAMENTS = {}
TOURNAMENT_LIST = []

USERNAME_TO_USR_DICT = {}
USR_TO_USERNAME = {}

Games_list = []
OTPS = {}
TOTAL_GAMES = 0

GAMES_collection = db["GAMES"]
GAMES_PLAYERS_collection = db["GAMES_PLAYERS"]
USER_COMM_DETAIL_collection = db["USER_COMM_DETAIL"]
OTPS_collection = db["OTPS"]
Users_collection =  db["USERS"]
TOURNAMENTS_collection = db["TOURNAMENTS"]

channel = SMSChannel.from_auth_params(
    {
        "base_url": OTP_URL,
        "api_key": API_KEY,
    }
)

def get_OTP():
    return (randint(1,9) * 1000) + (randint(1,9) * 100) + (randint(1,9) * 10) + randint(1,9)

def join(list_):
    f = "254"
    for i in list_:
        f += i
    return f

def push_OTP(OTP, RECIPIENT):
    RECIPIENT = str(RECIPIENT)
    if(RECIPIENT.startswith("0")):
        RECIPIENT = list(RECIPIENT)
        RECIPIENT.pop(0)
        RECIPIENT = join(RECIPIENT)
    sms_response = channel.send_sms_message(
    {
        "messages": [
            {
                "destinations": [{"to": RECIPIENT}],
                "text": f"Your Clutter verification otp is - {OTP}",
            }
        ]
    }
    )
    query_parameters = {"limit": 10}
    delivery_reports = channel.get_outbound_sms_delivery_reports(query_parameters)

def myfunction():
    x = (randint(1,3) / randint(4,9))
    return x


def distribute(CARD_Numbers):
    USERS_CARD_DICT = {
    "USR_0_CARDS" : [],
    "USR_1_CARDS" : [],
    "USR_2_CARDS" : [],
    "USR_3_CARDS" : []
    }
    for user in USERS_CARD_DICT.keys():
        user_cards = []
        for _ in range(3):
            user_cards.append(CARD_Numbers[0])
            CARD_Numbers.pop(0)
        USERS_CARD_DICT[user] = user_cards
    return USERS_CARD_DICT, CARD_Numbers


class USR_CLASS:
    def __init__(self):
        self.usr = 0
    
    def increase_usr(self):
        if(self.usr < 3):
            self.usr += 1
        else:
            self.usr = 0

    def get_usr(self):
        chs = self.usr
        if(self.usr < 3):
            self.usr += 1
        else:
            self.usr = 0
        return chs

USR_CLASS_OBJECT = USR_CLASS()

@app.route("/get_deck/<string:id>")
def get_deck(id):
    Game = GAMES[id]
    PickDeck = Game["Pick_Deck"]
    return jsonify({"DECK":PickDeck, "Top": Game["Top"]})

@app.route("/pick_single/<string:id>", methods=["POST"])
def pick_single(id):
    data = request.json
    usr_id = USERNAME_TO_USR_DICT[data["username"]]
    GAME_DETAILS = GAMES_collection.find_one({"id": id})
    arrangements = Player_arrangement[id]
    curr_arrangement = arrangements[data["username"]]
    if(GAME_DETAILS["Current_player"] != data["username"]):
         return jsonify({"success" : False})

    USERS_CARD_DICT = GAME_DETAILS["Cards"]
    user_cards = USERS_CARD_DICT[usr_id]
    CARD_Numbers = GAME_DETAILS["Pick_Deck"]
    dropped = GAME_DETAILS["Dropped"]
    if(len(CARD_Numbers) < 2):
        CARD_Numbers.extend(dropped)
        shuffle(CARD_Numbers, myfunction)
    user_cards.append(CARD_Numbers[0])
    CARD_Numbers.pop(0)
    # USERS_CARD_DICT[usr_id] = user_cards
    # GAME_DETAILS["Cards"] = USERS_CARD_DICT
    # GAME_DETAILS["Pick_Deck"] = CARD_Numbers
    # GAME_DETAILS["Dropped"] = []
    # GAMES[id] = GAME_DETAILS
    GAMES_collection.update_one({"id": id},{"$set": { "Cards": USERS_CARD_DICT, "Dropped": [] ,"Pick_Deck": CARD_Numbers }})
    emit("setPlayer", {"player": curr_arrangement[0]},namespace="/", broadcast=True)
    return jsonify({"CARDS" : user_cards, 'success': True,'PICKS': CARD_Numbers})

@app.route("/pick_two/<string:id>", methods=["POST"])
def pick_two(id):
    data = request.json
    usr_id = USERNAME_TO_USR_DICT[data["username"]]
    # GAME_DETAILS = GAMES[id]
    GAME_DETAILS = GAMES_collection.find_one({"id": id})
    arrangements = Player_arrangement[id]
    curr_arrangement = arrangements[data["username"]]
    if(GAME_DETAILS["Current_player"] != data["username"]):
         return jsonify({"success" : False})
    USERS_CARD_DICT = GAME_DETAILS["Cards"]
    user_cards = USERS_CARD_DICT[usr_id]
    CARD_Numbers = GAME_DETAILS["Pick_Deck"]
    dropped = GAME_DETAILS["Dropped"]

    if(len(CARD_Numbers) < 3):
        CARD_Numbers.extend(dropped)
        shuffle(CARD_Numbers, myfunction)
        user_cards.append(CARD_Numbers[0])
        user_cards.append(CARD_Numbers[1])
        CARD_Numbers.pop(0)
        CARD_Numbers.pop(0)
        USERS_CARD_DICT[usr_id] = user_cards
        GAME_DETAILS["Cards"] = USERS_CARD_DICT
        GAME_DETAILS["Pick_Deck"] = CARD_Numbers
        GAME_DETAILS["Dropped"] = []
        GAMES_collection.update_one({"id": id},{"$set": { "Cards": USERS_CARD_DICT, "Dropped": [] ,"Pick_Deck": CARD_Numbers }})
    else:
        user_cards.append(CARD_Numbers[0])
        user_cards.append(CARD_Numbers[1])
        CARD_Numbers.pop(0)
        CARD_Numbers.pop(0)
        USERS_CARD_DICT[usr_id] = user_cards
        GAME_DETAILS["Cards"] = USERS_CARD_DICT
        GAME_DETAILS["Pick_Deck"] = CARD_Numbers
        GAMES_collection.update_one({"id": id},{"$set": { "Cards": USERS_CARD_DICT,"Pick_Deck": CARD_Numbers }})
    # GAMES[id] = GAME_DETAILS
    emit("setPlayer", {"player": curr_arrangement[0]},namespace="/", broadcast=True)
    return jsonify({"CARDS" : user_cards,  "success": True,'PICKS': CARD_Numbers})


@app.route("/pick_three/<string:id>", methods=["POST"])
def pick_three(id):
    data = request.json
    usr_id = USERNAME_TO_USR_DICT[data["username"]]
    # GAME_DETAILS = GAMES[id]
    GAME_DETAILS = GAMES_collection.find_one({"id": id})
    arrangements = Player_arrangement[id]
    curr_arrangement = arrangements[data["username"]]
    if(GAME_DETAILS["Current_player"] != data["username"]):
         return jsonify({"success" : False})
    USERS_CARD_DICT = GAME_DETAILS["Cards"]
    user_cards = USERS_CARD_DICT[usr_id]
    CARD_Numbers = GAME_DETAILS["Pick_Deck"]
    dropped = GAME_DETAILS["Dropped"]
    if(len(CARD_Numbers) < 4):
        CARD_Numbers.extend(dropped)
        shuffle(CARD_Numbers, myfunction)
        user_cards.append(CARD_Numbers[0])
        user_cards.append(CARD_Numbers[1])
        user_cards.append(CARD_Numbers[2])
        CARD_Numbers.pop(0)
        CARD_Numbers.pop(0)
        CARD_Numbers.pop(0)
        USERS_CARD_DICT[usr_id] = user_cards
        GAME_DETAILS["Cards"] = USERS_CARD_DICT
        GAME_DETAILS["Pick_Deck"] = CARD_Numbers
        GAME_DETAILS["Dropped"] = []
        GAMES_collection.update_one({"id": id},{"$set": { "Cards": USERS_CARD_DICT, "Dropped": [] ,"Pick_Deck": CARD_Numbers }})
    else:
        user_cards.append(CARD_Numbers[0])
        user_cards.append(CARD_Numbers[1])
        user_cards.append(CARD_Numbers[2])
        CARD_Numbers.pop(0)
        CARD_Numbers.pop(0)
        CARD_Numbers.pop(0)
        USERS_CARD_DICT[usr_id] = user_cards
        GAME_DETAILS["Cards"] = USERS_CARD_DICT
        GAME_DETAILS["Pick_Deck"] = CARD_Numbers
        GAMES_collection.update_one({"id": id},{"$set": { "Cards": USERS_CARD_DICT,"Pick_Deck": CARD_Numbers }})
    # GAMES[id] = GAME_DETAILS
    emit("setPlayer", {"player": curr_arrangement[0]},namespace="/", broadcast=True)
    return jsonify({"CARDS" : user_cards, "success": True,'PICKS': CARD_Numbers})


# @app.route("/get_usr_id")
# def get_my_id():
#     curr_usr = USR_CLASS_OBJECT.get_usr()
#     usr_id = 'USR_' + str(curr_usr) + '_CARDS'
#     data = {'CARDS': USERS_CARD_DICT[usr_id] ,"success": True}
#     return jsonify(data)

@app.route("/get_cards/<string:curr_usr>", methods=["POST"])
def get_cards(curr_usr):
    data = request.json
    # GAME_DETAILS = GAMES[data["game_id"]]
    GAME_DETAILS = GAMES_collection.find_one({"id": data["game_id"]})
    arrangement = Player_arrangement[data["game_id"]]
    
    USERS_CARD_DICT = GAME_DETAILS["Cards"]
    usr_id = USERNAME_TO_USR_DICT[curr_usr]
    data = {'CARDS': USERS_CARD_DICT[usr_id], "arrangement": arrangement[curr_usr],"success": True}
    return jsonify(data)

# @app.route('/get_usr_cards/<string:id>')
# def get_usr_cards(id):
#     data = {'success': True, 'CARDS': USERS_CARD_DICT[id]}
#     return jsonify(data)

@app.route("/verify/<string:phone>", methods=["POST"])
def verify(phone):
    data = request.json
    OTP = data["OTP"]
    res = OTPS_collection.find_one({"phone": phone})
    if(res):
        if(res["OTP"] == OTP):
            return jsonify({"success": True})
        return jsonify({"success": False, "Message": f"The verification code does not match."})
    return jsonify({"success": False, "Message": f"The phone number {phone} does not exists."})


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    res = Users_collection.find_one({"phone": data["phone"] })
    if(res):
        usr = res["username"]
        return jsonify({"success": False, "Message": f"User with username {usr} exists."})
    else:
        data["balance"] = 100
        User_OTP = get_OTP()
        OTP_DICT = {}
        OTP_DICT["OTP"] = User_OTP
        OTP_DICT["phone"] = data["phone"]
        push_OTP(User_OTP, data["phone"])
        OTPS_collection.insert_one(OTP_DICT)
        Users_collection.insert_one(data)
        return jsonify({"success": True})


@app.route("/create_game", methods=["POST"])
def create_game():
    data = request.json
    CARD_Numbers = [0, 1,2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,14,15]
    shuffle(CARD_Numbers, myfunction)
    cards_dict, Pick_Deck = distribute(CARD_Numbers)
    game_id = str(uuid4())
    Top = Pick_Deck[0]
    Pick_Deck.pop(0)
    data["Id"] = game_id
    data["Top"] = Top
    data["Cards"] = cards_dict
    data["Is_Tournament"] = False
    data["Pick_Deck"] = Pick_Deck
    data["Current_player"] = ""
    data["Dropped"] = []
    data["Tittle"] = f"Game_00{randint(0,37)}"
    GAMES[game_id] = data
    GAME_PLAYERS[game_id] = []
    Games_list.append(data)
    if(Is_allowed["Value"]):
        GAMES_collection.insert_one(data)
        Is_allowed["Value"] = False
        return jsonify({"success": True, "game_id": game_id})
    return jsonify({"success": False, "Message": "You are not allowed to create another game befor the others are full"})


@app.route("/create_tournament", methods=["POST"])
def create_tournament():
    data = request.json
    players = int(data["players"])
    if(players <= 4 | players > 32 | players % 4 != 0):
        return jsonify({"success": False, "Message": "A tourament must have 8, 16 or 32 players"})
    groups = int(players/4)

    tourament_id = str(uuid4())
    created_games = []
    name = data["Tittle"]

    for i in range(groups):
        game_id = str(uuid4())
        new_game = {}
        new_game["Id"] = game_id
        new_game["Tournament"] = tourament_id
        new_game["Is_Tournament"] = True
        new_game["players"] = 4
        new_game["stake"] = data["stake"]
        data["Current_player"] = ""
        new_game["start_date"] = f"{randint(1,30)}/{randint(3,12)}/2023"
        new_game["registered_players"] = []
        new_game["Tittle"] = f"{name} - Game {i + 1}/{groups}"
        GAMES[game_id] = new_game
        GAME_PLAYERS[game_id] = []
        created_games.append(new_game)

    data["games"] = created_games
    data["Id"] = tourament_id
    data["Is_on"] = False
    TOURNAMENTS[tourament_id] = data
    TOURNAMENT_LIST.append(data)

    return jsonify({"success": True, "tourament_id": tourament_id})

@app.route("/get_games", methods=["GET"])
def get_games():
    Games_list = GAMES_collection.find({})
    all = []
    for item in Games_list:
        item["_id"] = str(item["_id"])
        all.append(item)
    return jsonify({"success": True, "games": all})

@app.route("/get_tournaments", methods=["GET"])
def get_tournaments():
    return jsonify({"success": True, "tournaments": TOURNAMENT_LIST})

@app.route("/get_tournament_games/<string:id>", methods=["GET"])
def get_tournament_games(id):
    TOURNAMENT_DETAILS = TOURNAMENTS[id]
    all_games = TOURNAMENT_DETAILS["games"]
    return jsonify({"success": True, "games": all_games})

@app.route("/get_game/<string:id>", methods=["GET"])
def get_game(id):
    GAME_DETAILS = GAMES_collection.find_one({"Id": id})
    GAME_DETAILS["_id"] = str(GAME_DETAILS["_id"])
    return jsonify({"success": True, "game": GAME_DETAILS})

@app.route("/get_current_player/<string:id>", methods=["GET"])
def get_current_player(id):
    # GAME_DETAILS = GAMES[id]
    GAME_DETAILS = GAMES_collection.find_one({"id": id})
    return jsonify({"Current_player":GAME_DETAILS["Current_player"]})

def next_player_arrangement(players, size, i=0, arrangement={}):
    if(len(players) < size):
        size = len(players)
    if(i > (size - 1)):
        return arrangement
    player = players[0]
    players.pop(0)
    new_players = players.copy()
    arrangement[player] = players
    i += 1
    new_players.append(player)
    return next_player_arrangement(new_players, size, i, arrangement)


@app.route("/enter_game/<string:id>", methods=["POST"])
def enter_game(id):
    try:
        # GAME_DETAILS = GAMES[id]
        GAME_DETAILS = GAMES_collection.find_one({"id": id})
        players = GAME_PLAYERS[id]
        player_idx = len(players)
        usr_id = 'USR_' + str(len(players)) + '_CARDS'
        data = request.json
        if(len(players) >=  int(GAME_DETAILS["players"]) and data["username"] not in players):
            Is_allowed["Value"] = True
            return jsonify({"success": False, "Message": "Game is at maximum capacity"})
        
        if(data["username"] in players):
            return jsonify({"success": True,"Current_player": GAME_DETAILS["Current_player"] ,"player_pos": player_idx,"game_id": id, "Players": len(players), "All_Player": players})
        if(GAME_DETAILS["Current_player"] == ""):
            GAME_DETAILS["Current_player"] = data["username"]
            GAMES_collection.insert_one(GAME_DETAILS)
            # GAMES[id] = GAME_DETAILS
        players.append(data["username"])
        arrangement = next_player_arrangement(players.copy(), int(GAME_DETAILS["players"]), 0, {})
        USERNAME_TO_USR_DICT[data["username"]] = usr_id
        GAME_PLAYERS[id] = players
        Player_arrangement[id] = arrangement
        return jsonify({"success": True,"Current_player": GAME_DETAILS["Current_player"] ,"player_pos": player_idx,"game_id": id, "Players": len(players), "All_Player": players})

    except ValueError:
        return jsonify({"success": False, "Message": "Game not found"})
    
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    res = Users_collection.find_one({"phone": data["phone"] })
    if(res):
        if(res["password"] == data["password"]):
            l_players = LoggedInPlayers['Total_online']
            l_players += 1
            LoggedInPlayers['Total_online'] = l_players
            emit("log", {"Count": l_players},namespace="/", broadcast=True)
            return jsonify({"success": True, "Username":data["phone"], "Count": l_players})
        return jsonify({"success": False, "Message": f"Incorrect password.Check and try again"})
    return jsonify({"success": False, "Message": f"User does not exist."})

@app.route("/get_user/<string:username>", methods=["GET"])
def get_user(username):
    res = Users_collection.find_one({"phone": username})
    res["_id"] = str(res["_id"])
    return jsonify({"success": True, "user":res})

@app.route("/get_players/<string:id>", methods=["GET"])
def get_players(id):
    players = GAME_PLAYERS[id]
    return jsonify({"success": True, "Players":players})

@app.route("/set_comm_data/<string:usr>", methods=["POST"])
def set_comm_data(usr):
    data = request.json
    USER_COMM_DETAILS[usr] = {"id": data["id"], "namespace": data["namespace"]}
    return jsonify({"id": data["id"], "namespace": data["namespace"]})

@app.route("/handle_drop/<string:card_id>", methods=["POST"])
def handle_drop(card_id):
    data = request.json
    pick_size = 1
    players = GAME_PLAYERS[data["game_id"]]
    idx = players.index(data["USR"])
    GAME_DETAILS = GAMES_collection.find_one({"id": data["game_id"]})
    Dropped = GAME_DETAILS["Dropped"]
    USER_CARDS_DICT = GAME_DETAILS["Cards"]
    usr_id = USERNAME_TO_USR_DICT[data["USR"]]
    User_cards = USER_CARDS_DICT[usr_id]
    card_idx = User_cards.index(int(card_id))
    if(idx < len(players) - 1):
        next_player = players[idx + 1]
    else:
        next_player = players[0]

    if(data["Action"] == "HOLD"):
        net_data = USER_COMM_DETAILS[next_player]
        Act = "WAIT"
        GAME_DETAILS["Current_player"] = next_player
    elif(data["Action"] == "PICK_MULTIPLE"):
        net_data = USER_COMM_DETAILS[next_player]
        GAME_DETAILS["Current_player"] = next_player
        Act = "PICK_MULTIPLE"
        pick_size = 2
    elif(data["Action"] == "JUMP"):
        if(idx < len(players) - 1):
            next_player = players[idx + 2]
        else:
            next_player = players[1]
        GAME_DETAILS["Current_player"] = next_player
        net_data = USER_COMM_DETAILS[next_player]
        Act = "WAIT"
    else:
        net_data = USER_COMM_DETAILS[data["USR"]]
        next_player = data["USR"]
        GAME_DETAILS["Current_player"] = data["USR"]
        Act = data["Action"]
    Dropped.append(card_id)
    emit("drop", {"Card_Id": int(card_id), "Player": data["USR"]},namespace="/", broadcast=True)
    if(Act == "TRIPLE_CONGRESS" or Act == "CONGRESS"):
        emit("setAction", {"Act": Act},namespace="/", broadcast=True)
    else:
        emit("setAction", {"Act": Act, "S": pick_size},namespace="/", room=net_data["id"])
    User_cards.pop(card_idx)
    if(len(User_cards) == 1 & int(card_id) >= 12):
        emit("onCard", {"Player": data["USR"], "index": idx},namespace="/", broadcast=True)
    emit("setPlayer", {"player": next_player},namespace="/", broadcast=True)
    USER_CARDS_DICT[usr_id] = User_cards
    # GAME_DETAILS["Cards"] = USER_CARDS_DICT
    # GAME_DETAILS["Top"] = int(card_id)
    # GAME_DETAILS["Dropped"] = Dropped
    # GAME_DETAILS["Current_player"] = next_player
    # GAMES[data["game_id"]] = GAME_DETAILS
    GAMES_collection.update_one({"id": data["game_id"]}, {"$set" : {"Current_player": next_player,"Dropped": Dropped,"Top": int(card_id),"Cards": USER_CARDS_DICT}})
    

    return jsonify({"Card_Id": int(card_id), "next_player": next_player})



@socketio.on("connect")
def connected():
    """event listener when client connects to the server"""
    ide = USR_CLASS_OBJECT.get_usr()
    USER_COMM_DETAILS[ide] = {"id": request.sid, "namespace": request.namespace}
    emit("connected",{"id": request.sid, "namespace": request.namespace, "usr": ide})

@socketio.on('data')
def handle_message(data):
    """event listener when client types a message"""
    print("data from the front end: ",str(data))
    emit("data",{'data':data,'id':request.sid},broadcast=True)



@socketio.on("disconnect")
def disconnected():
    """event listener when client disconnects to the server"""
    print("user disconnected")
    emit("disconnect",f"user {request.sid} disconnected",broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=False,port=5001,host="0.0.0.0")