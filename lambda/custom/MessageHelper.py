import math
import random
class Message_Helper:
    def __init__(self):
        self.message_status = Game_Message_Status.Invalid

    def get_message(self, intent, session, data = None):
        response = None

        if self.message_status == Game_Message_Status.Invalid:
            response = self.invalid_request()
        elif self.message_status == Game_Message_Status.Did_Not_Find_Item:
            response = self.did_not_find_item(intent, session)
        elif self.message_status == Game_Message_Status.On_Garden_Help:
            response = self.get_on_garden_help_response()
        elif self.message_status == Game_Message_Status.New_Game:
            response = self.handle_select_menu_option_intent(intent, session, "new")
        elif self.message_status == Game_Message_Status.Load_Game:
            response = self.handle_select_menu_option_intent(intent, session, "load")
        elif self.message_status == Game_Message_Status.Session_End_Request:
            response = self.handle_session_end_request()
        elif self.message_status == Game_Message_Status.On_Launch:
            response = self.get_welcome_response()
        elif self.message_status == Game_Message_Status.Fertilize:
            response = self.get_fertilize_response(data['number'], data['amount'])
        elif self.message_status == Game_Message_Status.Water:
            response = self.get_water_response(data['number'], data['amount'])
        elif self.message_status == Game_Message_Status.Do_Not_Have_Flower_In_Slot:
            response = self.get_do_not_have_flower_response()
        elif self.message_status == Game_Message_Status.Flower_Is_Dead or self.message_status == Game_Message_Status.Flower_Is_Fully_Growed:
            response = self.get_flower_is_dead_response()
        elif self.message_status == Game_Message_Status.Report:
            response = self.get_report_response(intent, data)
        elif self.message_status == Game_Message_Status.Load_Game_In_Garden:
            response = self.get_in_garden_load_response()
        elif self.message_status == Game_Message_Status.End_Of_Game:
            response = self.get_end_of_game_response(data['score'], data['old_score'])
        elif self.message_status == Game_Message_Status.Hint:
            response = self.get_hint_response()
        elif self.message_status == Game_Message_Status.Too_Much_Fertilizer_Warning:
            response = self.get_too_much_fertilizer_warning(data['number'],data['amount'])
        elif self.message_status == Game_Message_Status.Too_Much_Water_Warning:
            response = self.get_too_much_water_warning(data['number'], data['amount'])
        elif self.message_status == Game_Message_Status.Dig:
            response = self.get_dig_response(data['number'], data['amount'])
        elif self.message_status == Game_Message_Status.Pour:
            response = self.get_pour_response(data['number'], data['amount'])
        elif self.message_status == Game_Message_Status.Pause:
            response = self.get_pause_response()
        elif self.message_status == Game_Message_Status.Bird_Spreading:
            response = self.get_bird_spreading_response()
        elif self.message_status == Game_Message_Status.Check_Score:
            response = self.get_check_score_response(data['score'], data['highest_score'])
        elif self.message_status == Game_Message_Status.New_Flower_Stage:
            response = self.get_new_flower_stage_response()
        self.message_status = Game_Message_Status.Invalid

        return response

# --------------- Helpers that build all of the responses ----------------------
    def build_speechlet_response(self, title, output, reprompt_text, should_end_session, card_cont=None):
        if card_cont is None:
            card_cont = output
        if reprompt_text == None:
            reprompt_text = "if we don't have more tasks to do, you can say stop to save your game, or the game will end without saving"
        
        return {
        'outputSpeech': {
            "type": "SSML",
            "ssml": "<speak>" + output + "</speak>"
        },
        'card': {
            'type': 'Simple',
            'title':  title,
            'content': card_cont
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

    def build_response(self, session_attributes, speechlet_response):
        return {
            'version': '1.0',
            'sessionAttributes': session_attributes,
            'response': speechlet_response
        }

    # --------------Intent handling functions
    def quick_build(self, card_title, card_cont, speech_output, repormt_text, session_attributes, session_should_end = False):
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repormt_text, session_should_end, card_cont))
    
    def get_check_score_response(self, score, high):
        text = 'your current score is ' + str(score) + ', and your highest score is ' + str(high)
        return self.quick_build('score', text, text, None, None, False)

    def get_pause_response(self):
        text = 'your game is paused until the next time you start your game'
        return self.quick_build('game paused', text, text, None, None, True)
    
    def get_pour_response(self, number, amount):
        text = "flower number " + str(number) + ' now has ' + str(math.floor(amount*1000) / 10) + ' percent of water '
        return self.quick_build('pour', text, "<audio src=\"https://s3.amazonaws.com/mylittlegarden/pour.mp3\" />" + text, None, None, False)
    
    def get_new_flower_stage_response(self):
        audio = None
        if random.randint(1,2) == 1:
            audio = "<audio src=\"https://s3.amazonaws.com/mylittlegarden/open1.mp3\" />"
        else :
            audio = "<audio src=\"https://s3.amazonaws.com/mylittlegarden/open2.mp3\" />"
        text = 'congradulation! some of your flowers just entered a new stage!'
        return self.quick_build('new stage!', text, audio + text, None, None, False)

    def get_dig_response(self, number, amount):
        text = "flower number " + str(number) + ' now has ' + str(math.floor(amount*1000) / 10) + ' percent of fertilizer '
        return self.quick_build('dig', text, "<audio src=\"https://s3.amazonaws.com/mylittlegarden/dig.mp3\" />" + text, None, None, False)

    def get_too_much_water_warning(self, number, amount):
        return self.quick_build('warning', None, 'too much water on flower number ' + str(number) + ', it currently has ' + str(math.floor(amount*1000) / 10) + ' percent of water, try pouring out some water or the flowers will be drowned', None, None)

    def get_too_much_fertilizer_warning(self, number, amount):
        return self.quick_build('warning', None, 'flower number ' + str(number) + ' has ' + str(math.floor(amount*1000) / 10) + " percent of fertilizer that's too much! try digging out some of your fertilizer or the flowers will be poisoned", None, None)
    
    def get_bird_spreading_response(self):
        text = 'a birds just droped a seeds in your garden!'
        return self.quick_build("It's The Bird!", text, '<audio src=\"https://s3.amazonaws.com/mylittlegarden/spreading.mp3\" />' + text, None, None, False)
    
    def get_hint_response(self):
        hints = [
            'fertilizer influences the possibility of seeds generation when flowers are in the spreading stage, so, keep your fertilizer as much as possible to one hundred percent',
            'if the seeds generated at the spreading stage exceeds the capability, the exceeded amount will become your scores',
            'there is possibility that during some periods a bird will help you plan a seed, be expected for that!',
            'flowers will be dried out or drowned if you have too little or too much water',
            "when a flower is in spreading stage, check your flowers more frequently than before, you don't want it pass away without reproducing any seeds",
            'watering and fertilizing can increase water and fertilizer by 10 percent',
            'pouring and digging can decrease water and fertilizer by 10 percent'
        ]

        size = len(hints) - 1
        speech_output = hints[random.randint(0, size)]
        return self.quick_build('hint', None, speech_output, None, None)

    def get_in_garden_load_response(self):
        session_attributes = {}
        card_title = 'reload'
        speech_output = 'you have loaded your last checkpoint'
        repormt_text = None
        should_end_session = False
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repormt_text, should_end_session))
    
    def get_end_of_game_response(self, score, old_score):
        speech_output = 'all your flowers are not reproducible, you reached the end of the game, the score is ' + str(score) + ', your previous highest score is ' + str(old_score)
        if score > old_score:
            speech_output += ', congradulations, you have become a better little flower manager'
        else:
            speech_output += ', thanks for playing!' +' to start a new game just say open my garden'

        return self.quick_build('end of game', None, speech_output , None, None, True)

    def get_report_response(self, intent, flower_data):
        session_attributes = {}
        card_title = 'report'
        speech_output = None
        repormt_text = None
        should_end_session = False

        if 'value' in intent['slots']['number']:
            number = intent['slots']['number']['value']
            if int(number) < 1 or int(number) > 3:
                speech_output = "flower number doesn't exist"
            else:
                name = 'flower' + str(number)
                speech_output = self.build_flower_str(name, flower_data, number)
        else:
            speech_output = ''
            for n in range(1,4):
                name = 'flower' + str(n)
                speech_output += self.build_flower_str(name, flower_data, name[-1:])
            speech_output = speech_output[:-2]
        
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repormt_text, should_end_session))
    
    def build_flower_str(self, name, flower_data, number):
        water_amount = float(flower_data[name]['water_amount']) * 100
        fertilizer_amount = float(flower_data[name]['fertilizer_amount']) * 100
        stage_str = self.stage_to_text(flower_data[name]['stage'], flower_data['stages'])
        if stage_str != 'null':
            speech_output = 'flower ' + str(number) + ' is in ' + stage_str + ' stage, with ' + str(math.floor(water_amount*10)/10) + ' percent of water and, ' + str(math.floor(fertilizer_amount*10)/10) + ' percent of fertilizer, '
        else:
            speech_output = ''
        return speech_output
    
    def stage_to_text(self, stage, stages_data):
        if stage == stages_data[1]:
            return 'seed'
        elif stage == stages_data[2]:
            return 'germination'
        elif stage == stages_data[3]:
            return 'spreading'
        else:
            return 'null'
    
    def get_on_garden_help_response(self):
        session_attributes = {}
        card_title = 'help'
        speech_output = "you can say, report, to check your garden status and then try, water, fertilize, pour out, dig out, to manage your flower conditions. For more infomation, please see game instructions"
        repormt_text = None
        should_end_session = False
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repormt_text, should_end_session))

    def get_do_not_have_flower_response(self):
        session_attributes = {}
        card_title = 'no flower in slots~'
        speech_output = "you currently don't have flower in that slot"
        repormt_text = None
        should_end_session = False
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repormt_text, should_end_session))

    def invalid_request(self):
        session_attributes = {}
        card_title = 'invalid request'
        ran = random.randint(0,3)
        speech_output = None
        if ran == 0:
            speech_output = 'sorry, I may miss that, could you say again?'
        else:
            speech_output = "that may be a invalid request"
        repormt_text = "if you don't know what options you can have, you can say help"
        should_end_session = False
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repormt_text, should_end_session))

    def did_not_find_item(self, intent, session):
        session_attributes = session['attributes']
        card_title = 'user not found'
        speech_output = "it seems like you don't have any game in progress"
        should_end_session = False
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, None, should_end_session))
    
    def handle_select_menu_option_intent(self, intent, session, option):
        speech_output = None
        audio_speech_output = None
        session_attributes = {"status" : "on_garden"}
        repormt_text = "do you want me to report your garden, or start to water or fertilize your flowers"
        should_end_session = False
        card_title = "on garden"
        if option == "new":
            speech_output = "I have built a new garden for you, remember to check your flowers before you leave"
            return self.quick_build(card_title, speech_output, speech_output,repormt_text, None, False)
        elif option == "load":
            audio = None
            if random.randint(1,2) == 1:
                audio = "<audio src=\"https://s3.amazonaws.com/mylittlegarden/open1.mp3\" />"
            else :
                audio = "<audio src=\"https://s3.amazonaws.com/mylittlegarden/open2.mp3\" />"
            speech_output = audio + "welcome back"
            return self.quick_build(card_title, "welcome back", speech_output, repormt_text, None, False)

    def get_flower_is_dead_response(self):
        session_attributes = {}
        speech_output = "one or more flowers are dead due to the water amount or the fertilizer amount or it's just fully growed and removed Say report to know the current situation"
        repromt_text = None
        should_end_session = False
        card_title = "one or more flowers are dead"
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repromt_text, should_end_session))

    def get_fertilize_response(self, number, amount):
        speech_output = "<audio src=\"https://s3.amazonaws.com/mylittlegarden/fertilize.mp3\" />"
        text = "your flower number " + str(number) + " now has " + str(math.floor(amount*1000) / 10) + " percent of fertilizer"
        return self.quick_build('fertilize', text, speech_output + text, None, None, False)

    def get_water_response(self, number, amount):
        speech_output = "<audio src=\"https://s3.amazonaws.com/mylittlegarden/water.mp3\" />"
        text = "flower number " + str(number) + ' now has ' + str(math.floor(amount*1000) / 10) + ' percent of water'
        return self.quick_build('water', text, speech_output + text, None, None, False)

    def get_menu_help(self, session):
        """

        """
        session_attributes = None
        speech_output = "you can say \"new game\" or \"load game\""
        repromt_text = "ummm, I didn't hear anything you can say \"new game\", \"load game\""
        should_end_session = False
        card_title = "menu_help"
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repromt_text, should_end_session))

    def get_garden_help(self, session):
        session_attributes = None
        speech_output = "you can say \"go to shop\" or \"spray flowers\""
        repromt_text = "you can say \"go to shop\" or \"spray flowers\""
        should_end_session = False
        card_title = "garden_help"
        return self.build_response(session_attributes, self.build_speechlet_response(card_title, speech_output, repromt_text, should_end_session))

    def get_help_response(self, intent, session):
        """

        """
        if session["attributes"]["status"] == "on_menu":
            return self.get_menu_help(session)
        elif session["attributes"]["status"] == "on_garden":
            return self.get_garden_help(session)

    def get_welcome_response(self):
        """ If we wanted to initialize the session to have some attributes we could
        add those here
        """

        session_attributes = {"status": "on_menu"}
        card_title = "Welcome"
        speech_output = "Welcome to your little garden. " \
                        "What do you want to do right now? "
        # If the user either does not reply to the welcome message or says something
        # that is not understood, they will be prompted again with this text.
        reprompt_text = None

        should_end_session = False
        return self.build_response(session_attributes, self.build_speechlet_response(
            card_title, speech_output, reprompt_text, should_end_session))        

    def handle_session_end_request(self):
        card_title = "game ends with saving"
        speech_output = "I have saved your progress! see you next time!"
        # Setting this to true ends the session and exits the skill.
        should_end_session = True
        return self.build_response({}, self.build_speechlet_response(
            card_title, speech_output, None, should_end_session))
    
    def unrecognized_reuqest(self):
        card_title = "unrecognized"
        speech_output = "I don't know that, please try again"
        return self.quick_build(card_title, None, speech_output, None, None, False)
class Game_Message_Status:
    Invalid = 0
    Did_Not_Find_Item = 1
    #Help = 2
    New_Game = 3
    Session_End_Request = 4
    Game_Is_Loaded = 5
    Game_Loading_Failed = 6
    New_Game_Start = 7
    On_Launch = 8
    Fertilize = 9
    Water = 10
    Do_Not_Have_Flower_In_Slot = 11
    Flower_Is_Dead = 12
    Flower_Is_Fully_Growed = 13
    On_Menu_Help = 14
    On_Garden_Help = 15
    One_Seed_Generated = 16
    Two_Seed_Generated = 17
    End_Of_Game = 18
    Load_Game = 19
    Report = 20
    Load_Game_In_Garden = 21
    Hint = 22
    Too_Much_Water_Warning = 23
    Too_Much_Fertilizer_Warning = 24
    Dig = 25
    Pour = 26
    Pause = 27
    Bird_Spreading = 28
    Check_Score = 29
    New_Flower_Stage = 30