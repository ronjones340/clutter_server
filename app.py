from flask import Flask, request,jsonify
from flask_socketio import SocketIO,emit
from flask_cors import CORS
from random import shuffle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'AEF25993SACTFUWOPLMSFEWUHJAFQLP9873!'
CORS(app,resources={r"/*":{"origins":"*"}})
socketio = SocketIO(app,cors_allowed_origins="*")
CARD_Numbers = [0, 1,2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,14,15]

USERS_CARD_DICT = {
    "USR_0_CARDS" : [],
    "USR_1_CARDS" : [],
    "USR_2_CARDS" : [],
    "USR_3_CARDS" : []
}
USER_COMM_DETAILS = {}
Picked_List = []

def myfunction():
  return 0.589

shuffle(CARD_Numbers, myfunction)

def distribute(cards):
    for user in USERS_CARD_DICT.keys():
        user_cards = []
        for _ in range(3):
            user_cards.append(CARD_Numbers[0])
            CARD_Numbers.pop(0)
        USERS_CARD_DICT[user] = user_cards

distribute(CARD_Numbers)

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

@app.route("/get_deck")
def get_deck():
    data = {"DECK": CARD_Numbers}
    return jsonify(data)

@app.route("/pick_single/<string:id>")
def pick_single(id):
    usr_id = 'USR_' + str(id) + '_CARDS'
    user_cards = USERS_CARD_DICT[usr_id]
    user_cards.append(CARD_Numbers[0])
    CARD_Numbers.pop(0)
    USERS_CARD_DICT[usr_id] = user_cards
    return jsonify({"CARDS" : user_cards, 'PICKS': CARD_Numbers})

@app.route("/pick_two/<string:id>")
def pick_two(id):
    usr_id = 'USR_' + str(id) + '_CARDS'
    user_cards = USERS_CARD_DICT[usr_id]
    user_cards.append(CARD_Numbers[0])
    user_cards.append(CARD_Numbers[1])
    CARD_Numbers.pop(0)
    CARD_Numbers.pop(0)
    USERS_CARD_DICT[usr_id] = user_cards
    return jsonify({"CARDS" : user_cards, 'PICKS': CARD_Numbers})

@app.route("/pick_three/<string:id>")
def pick_three(id):
    usr_id = 'USR_' + str(id) + '_CARDS'
    user_cards = USERS_CARD_DICT[usr_id]
    user_cards.append(CARD_Numbers[0])
    user_cards.append(CARD_Numbers[1])
    user_cards.append(CARD_Numbers[2])
    CARD_Numbers.pop(0)
    CARD_Numbers.pop(0)
    CARD_Numbers.pop(0)
    USERS_CARD_DICT[usr_id] = user_cards
    return jsonify({"CARDS" : user_cards, 'PICKS': CARD_Numbers})


@app.route("/get_usr_id")
def get_my_id():
    curr_usr = USR_CLASS_OBJECT.get_usr()
    usr_id = 'USR_' + str(curr_usr) + '_CARDS'
    data = {'CARDS': USERS_CARD_DICT[usr_id] ,"success": True}
    return jsonify(data)

@app.route("/get_cards/<string:curr_usr>")
def get_cards(curr_usr):
    # curr_usr = USR_CLASS_OBJECT.get_usr()
    usr_id = 'USR_' + str(curr_usr) + '_CARDS'
    data = {'CARDS': USERS_CARD_DICT[usr_id] ,"success": True}
    return jsonify(data)

@app.route('/get_usr_cards/<string:id>')
def get_usr_cards(id):
    data = {'success': True, 'CARDS': USERS_CARD_DICT[id]}
    return jsonify(data)

@app.route("/handle_drop/<string:card_id>", methods=["POST"])
def handle_drop(card_id):
    data = request.json
    pick_size = 1
    if(data["Action"] == "HOLD"):
        net_data = USER_COMM_DETAILS[data['USR'] + 1]
        Act = "WAIT"
    elif(data["Action"] == "PICK_MULTIPLE"):
        net_data = USER_COMM_DETAILS[data['USR'] + 1]
        Act = "PICK_MULTIPLE"
        pick_size = 2
    elif(data["Action"] == "JUMP"):
        net_data = USER_COMM_DETAILS[data['USR'] + 2]
        Act = "WAIT"
    else:
        net_data = USER_COMM_DETAILS[data['USR']]
        Act = data["Action"]
    Picked_List.append(card_id)
    emit("drop", {"Card_Id": int(card_id)},namespace="/", broadcast=True)
    if(Act == "TRIPLE_CONGRESS" or Act == "CONGRESS"):
        emit("setAction", {"Act": Act},namespace="/", broadcast=True)
    else:
        emit("setAction", {"Act": Act, "S": pick_size},namespace="/", room=net_data["id"])

    return jsonify({"Card_Id": int(card_id)})


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