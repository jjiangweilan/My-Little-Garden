from MessageHelper import *
from decimal import Decimal
import random
import time
import boto3
import hashlib
    # ------------- Game -------------------
class Game:    
    def __init__(self):
        self.message_helper = Message_Helper()
        self.flowers = {}
        self.last_time = None
        self.score = 0
        dynamodb_resource = boto3.resource('dynamodb')
        self.dbtable = dynamodb_resource.Table('gardenDB')
        self.old_score = 0
        self.game_loaded = False
        self.highest_score = 0

    def load_game(self, intent, session):
        self.game_loaded = True
        time = self.load_flowers(intent, session)
        if self.message_helper.message_status == Game_Message_Status.Did_Not_Find_Item:
            self.new_game(intent,session)
            self.message_helper.message_status = Game_Message_Status.New_Game
            self.last_time = time
            return
        else:
            self.message_helper.message_status = Game_Message_Status.Load_Game

        user_item = self.get_user_item(session)
        paused = user_item['pause']
        if not paused: self.update_flowers(intent, session, time)
        end = self.end_of_game(session)
        if not end:
            self.bird_spreading(time - self.last_time)
        
        self.last_time = time

    def unrecognized_reuqest(self):
        return self.message_helper.unrecognized_reuqest(self)

    def get_user_item(self, session):
        m = hashlib.sha1()
        m.update(str(session['user']['userId']).encode('utf-8'))
        user_item = self.dbtable.get_item(
                Key={'userid': m.hexdigest()}
        )

        return user_item['Item']
    def get_one_empty_slot_name(self):
        for n in range(1,4):
            name = 'flower' + str(n)
            
    def update_flowers(self, intent, session, current_time):
        seeds_generated = 0
        for n in range(1, 4):
            name = 'flower' + str(n)
            if self.flowers[name].stage != Flower_Stage.NULL:
                message_status = self.flowers[name].time_step(current_time - self.last_time)
                seeds_generated = self.process_message_status_returned_from_time_step(message_status)
                if message_status is not None:
                    self.message_helper.message_status = message_status

        self.plan(seeds_generated)
        
    def end_of_game(self, session):
        for name in self.flowers:
            if self.flowers[name].stage != Flower_Stage.NULL:
                return False
        
        m = hashlib.sha1()
        m.update(str(session['user']['userId']).encode('utf-8'))
        self.message_helper.message_status = Game_Message_Status.End_Of_Game
        self.dbtable.delete_item(Key={'userid': m.hexdigest()})

        return True

    def plan(self, seeds):
        for n in range(seeds):
            for name in self.flowers:
                if self.flowers[name].stage == Flower_Stage.NULL:
                    self.flowers[name] = Flower(name)
                    self.flowers[name].stage = Flower_Stage.SEED
                    seeds -= 1
                    break
            if seeds <= 0:
                break

        self.score += seeds

    def bird_spreading(self, delta):
        count = 0
        stage = Flower_Stage.NULL
        for name in self.flowers:
            if self.flowers[name].stage != Flower_Stage.NULL:
                count += 1
                stage = self.flowers[name].stage
        
        if count == 1:
            if ((delta / 86400) > 0.4) and (stage == Flower_Stage.GERMINATION or stage == Flower_Stage.GROWTH):
                if random.uniform(0.0, 1.0) < 0.23:
                    for name in self.flowers:
                        if self.flowers[name].stage == Flower_Stage.NULL:
                            self.flowers[name] = Flower(name)
                            self.flowers[name].stage = Flower_Stage.SEED
                            self.message_helper.message_status = Game_Message_Status.Bird_Spreading
                            break

        
    def process_message_status_returned_from_time_step(self, message_status):
        seeds_generated = 0
        if message_status == Game_Message_Status.Flower_Is_Fully_Growed:
            self.score += 1
        elif message_status == Game_Message_Status.One_Seed_Generated:
            self.score += 1
            seeds_generated += 1
        elif message_status == Game_Message_Status.Two_Seed_Generated:
            self.score += 1
            seeds_generated += 2
        elif message_status == Game_Message_Status.Flower_Is_Dead:
            pass
        return seeds_generated

    def load_flowers(self, intent, session):
        #query dynamodb
        #if database doesn't contain userid information
        #then set the messge status to inform message helper to return coresponding user_item
        m = hashlib.sha1()
        m.update(str(session['user']['userId']).encode('utf-8'))
        user_item = self.dbtable.get_item(
                Key={'userid': m.hexdigest()}
        )
        current_time = time.time()

        if 'Item' in user_item:
            item = user_item['Item']
            self.last_time = float(item['last_time'])
            self.score = int(item['score'])
            self.old_score = int(item['score'])
            self.highest_score = int(item['highest_score']) if 'highest_score' in item else 0

            #for all slots
            #if there is data for the flower then load the flower to flowers array and update its attributes
            #if there is not, then add a flower with Null Status
            for n in range(1, 4):
                name = "flower" + str(n)
                if name in item:
                    flower_data = item[name]
                    self.add_flower(name, flower_data)
                else:
                    flower = Flower(name)
                    self.flowers[name] = flower

        else:
            self.message_helper.message_status = Game_Message_Status.Did_Not_Find_Item

        return current_time
    def new_game(self, intent, session):
        """
        delete user's current data
        start a new game by appending new flowers to self.flowers
        and new last_time
        """
        m = hashlib.sha1()
        m.update(str(session['user']['userId']).encode('utf-8'))
        
        self.dbtable.delete_item(Key={'userid': m.hexdigest()})

        for n in range(1,4):
            name = 'flower' + str(n)
            self.flowers[name] = Flower(name)

        self.flowers['flower1'].stage = Flower_Stage.SEED
        self.score = 0
        self.last_time = time.time()
    
    def message(self, intent, session):
        """
        generate game message
        called by update
        """
        intent_name = intent['name']

        if intent_name == Intent_Name.help_intent:
            self.message_helper.message_status = Game_Message_Status.On_Garden_Help
        elif intent_name == Intent_Name.new_game:
            self.message_helper.message_status = Game_Message_Status.New_Game
        elif intent_name == Intent_Name.load_game:
            self.message_helper.message_status = Game_Message_Status.Load_Game_In_Garden
        elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
            self.message_helper.message_status = Game_Message_Status.Session_End_Request
        elif intent_name == Intent_Name.fertilize:
            self.message_helper.message_status = Game_Message_Status.Fertilize
        elif intent_name == Intent_Name.water:
            self.message_helper.message_status = Game_Message_Status.Water
        elif intent_name == Intent_Name.report:
            self.message_helper.message_status = Game_Message_Status.Report
        elif intent_name == Intent_Name.hint:
            self.message_helper.message_status = Game_Message_Status.Hint
        elif intent_name == Intent_Name.pour:
            self.message_helper.message_status = Game_Message_Status.Pour
        elif intent_name == Intent_Name.dig:
            self.message_helper.message_status = Game_Message_Status.Dig
        elif intent_name == Intent_Name.pause:
            self.message_helper.message_status = Game_Message_Status.Pause
        elif intent_name == Intent_Name.check:
            self.message_helper.message_status = Game_Message_Status.Check_Score

    def launch(self, intent, session):
        self.load_game(intent, session)
        data = None
        if self.message_helper.message_status == Game_Message_Status.End_Of_Game:
            data = {
                'score': self.score,
                'old_score': self.old_score
            }
        return self.message_helper.get_message(intent, session, data)

    def game_update(self, intent, session):
        """
        update everything that relates to game rather than echo response
        """
        if intent['name'] == Intent_Name.new_game:
            self.new_game(intent,session)
        elif intent['name'] == Intent_Name.load_game:
            self.load_game(intent,session)
        elif intent['name'] == Intent_Name.water:
            self.water(intent, session)
        elif intent['name'] == Intent_Name.fertilize:
            self.fertilize(intent, session)
        elif intent['name'] == Intent_Name.pour:
            self.pour(intent, session)
        elif intent['name'] == Intent_Name.dig:
            self.dig(intent, session)
        elif intent['name'] == Intent_Name.stop_intent or intent['name'] == Intent_Name.cancel_intent:
            self.end(intent,session, False, False)
        elif intent['name'] == Intent_Name.pause:
            self.end(intent, session, False, True)

    def add_flower(self, name, data):
        stage = int(data['stage'])
        fer = float(data['fertilizer_amount'])
        wat = float(data['water_amount'])
        age = float(data['age'])
        call_time = float(data['call_time'])
        tot = float(data['total_fertilizer_amount'])

        flower = Flower(name, stage, fer, wat, age, call_time, tot)
        self.flowers[name] = flower

    def get_error(self):
        self.message_helper.message_status == Game_Message_Status.Invalid
        return self.message_helper.invalid_request()

    def pour(self,intent, session):
        slot_number, amount = self.get_slot_number_and_amount(intent)
        name = 'flower' + str(slot_number)
        if self.flowers[name].stage != Flower_Stage.NULL:
            self.flowers[name].pour(amount)
            if self.flowers[name].water_amount > 1.01:
                self.message_helper.message_status = Game_Message_Status.Too_Much_Water_Warning
        else:
            self.message_helper.message_status = Game_Message_Status.Do_Not_Have_Flower_In_Slot
        
       

    def dig(self,intent, session):
        slot_number, amount = self.get_slot_number_and_amount(intent)
        name = 'flower' + str(slot_number)
        if self.flowers[name].stage != Flower_Stage.NULL:
            self.flowers[name].dig(amount)
            if self.flowers[name].fertilizer_amount > 1.01:
                self.message_helper.message_status = Game_Message_Status.Too_Much_Fertilizer_Warning
        else:
            self.message_helper.message_status = Game_Message_Status.Do_Not_Have_Flower_In_Slot
        
        

    def water(self, intent, session):
        slot_number, amount = self.get_slot_number_and_amount(intent)
        name = 'flower' + str(slot_number)
        if self.flowers[name].stage != Flower_Stage.NULL:
            self.flowers[name].water(amount)
            if self.flowers[name].water_amount > 1.01:
                self.message_helper.message_status = Game_Message_Status.Too_Much_Water_Warning
        else:
            self.message_helper.message_status = Game_Message_Status.Do_Not_Have_Flower_In_Slot
        
        

    def fertilize(self, intent, session):
        slot_number, amount = self.get_slot_number_and_amount(intent)
        name = 'flower' + str(slot_number)
        if self.flowers[name].stage != Flower_Stage.NULL:
            self.flowers[name].fertilize(amount)
            if self.flowers[name].fertilizer_amount > 1.01:
                self.message_helper.message_status = Game_Message_Status.Too_Much_Fertilizer_Warning
        else:
            self.message_helper.message_status = Game_Message_Status.Do_Not_Have_Flower_In_Slot

        

    def get_slot_number_and_amount(self, intent):
        slot_number = None
        amount = None
        if 'value' in intent['slots']['SlotNumber']: slot_number = intent['slots']['SlotNumber']['value'] 
        else: raise GardenError('no flower slot number')
        if 'value' in intent['slots']['Times']: amount = intent['slots']['Times']['value']
        else: raise GardenError('no amount')
    
        return slot_number, amount
    def end(self, intent, session, rtn, pause):
        current_time = time.time()
        self.update_flowers(intent, session, current_time)
        self.last_time = current_time

        if not pause : self.message_helper.message_status = Game_Message_Status.Session_End_Request
        m = hashlib.sha1()
        m.update(str(session['user']['userId']).encode('utf-8'))
        item = {
            'userid': m.hexdigest()
        }
        
        for n in range(1, 4):
            name = 'flower' + str(n)
            item[name] = self.build_flower_item(name)
        
        item['pause'] = pause
        item['last_time'] = Decimal('{}'.format(self.last_time))
        item['score'] = self.score
        item['highest_score'] = self.score if self.score > self.highest_score else self.highest_score

        self.dbtable.put_item(
            Item = item
        )

        if rtn : return self.message_helper.get_message(intent, session)

    def build_flower_item(self, name):
        return {
            'stage' : self.flowers[name].stage,
            'fertilizer_amount' : Decimal('{}'.format(self.flowers[name].fertilizer_amount)),
            'water_amount' : Decimal('{}'.format(self.flowers[name].water_amount)),
            'age' : Decimal('{}'.format(self.flowers[name].age)),
            'call_time' : Decimal('{}'.format(self.flowers[name].call_time)),
            'total_fertilizer_amount' : Decimal('{}'.format(self.flowers[name].total_fertilizer_amount))
        }

    def update(self, intent, session):
        """
        message function alert the message status to the excepted status
        game_update function may alert the status to the unexcepted status
        ex: game is not successfully loaded
        """
        
        if self.game_loaded == False:
            self.load_game(intent, session)
        self.message(intent, session)
        self.game_update(intent, session)


        #pass nessary data to message_helper
        #report
        data = None
        if intent['name'] == Intent_Name.report: #game should be already loaded
            data = {}
            data['stages'] = [Flower_Stage.NULL, Flower_Stage.SEED, Flower_Stage.GERMINATION, Flower_Stage.GROWTH, Flower_Stage.SPREADING]
            for n in range(1, 4):
                name = 'flower' + str(n)
                data[name] = self.build_flower_item(name)

        #end of game
        elif self.message_helper.message_status == Game_Message_Status.End_Of_Game:
            data = {
                'score': self.score,
                'old_score': self.old_score
            }

        #water
        elif self.message_helper.message_status == Game_Message_Status.Water or self.message_helper.message_status == Game_Message_Status.Too_Much_Water_Warning or self.message_helper.message_status == Game_Message_Status.Pour:
            number = intent['slots']['SlotNumber']['value']
            name = 'flower' + str(number)
            data = {
                'number' : number,
                'amount' : self.flowers[name].water_amount
            }

        #fertilizer
        elif self.message_helper.message_status == Game_Message_Status.Fertilize or self.message_helper.message_status == Game_Message_Status.Too_Much_Fertilizer_Warning or self.message_helper.message_status == Game_Message_Status.Dig:
            number = intent['slots']['SlotNumber']['value']
            name = 'flower' + str(number)
            data = {
                'number' : number,
                'amount' : self.flowers[name].fertilizer_amount
            }

        elif self.message_helper.message_status == Game_Message_Status.Check_Score:
            highest = self.highest_score
            if self.score > self.highest_score:
                highest = self.score
            data = {
                'score' : self.score,
                'highest_score' : highest
            }
            
        return self.message_helper.get_message(intent, session, data)
    


    # --------------- flower ----------------------
class Flower_Stage:
    NULL = -1
    
    SEED = 0
    
    GERMINATION = 2
    
    GROWTH = 6
    
    SPREADING = 11

    DEATH = 16
    
class Flower:
    def __init__(self, name, stage = Flower_Stage.NULL, fer = None, wat = None, age = 0.01, call_time = 0, tot = 0.1):
        if fer is None:
            fer = round(random.uniform(0.2,0.6),1)
        if wat is None:
            wat = round(random.uniform(0.2, 0.6),1)
        self.stage = stage
        self.name = name
        self.fertilizer_amount = fer
        self.water_amount = wat
        self.age = age
        self.call_time = call_time
        self.total_fertilizer_amount = tot

    def water(self, amount):
        self.water_amount += (0.1 * float(amount))

    def fertilize(self, amount):
        self.fertilizer_amount += (0.1 * float(amount))

    def pour(self, amount):
        self.water_amount -= (0.1 * float(amount))
        if self.water_amount < 0: self.water_amount = 0

    def dig(self,amount):
        self.fertilizer_amount -= (0.1 * float(amount))
        if self.fertilizer_amount < 0 : self.fertilizer_amount = 0

    def time_step(self, delta_time):
        #24 hours = 1 step
        step_past = delta_time / 86400
        #water
        self.water_amount -= random.uniform(0.2, 0.5) * step_past
        
        #fertilizer
        self.fertilizer_amount -= random.uniform(0.1, 0.25) * step_past
        if self.fertilizer_amount < 0: self.fertilizer_amount = 0
        return self.grow(step_past)


    def grow(self, step_past):
        self.age += random.uniform(0.8, 1.5) * step_past
        self.call_time += 1
        self.total_fertilizer_amount += self.fertilizer_amount
        old_stage = self.stage
        message_status = None

        if Flower_Stage.SEED < self.age and self.age < Flower_Stage.GERMINATION:
            self.stage = Flower_Stage.SEED
        elif Flower_Stage.GERMINATION < self.age and self.age < Flower_Stage.GROWTH:
            self.stage = Flower_Stage.GERMINATION
        elif Flower_Stage.GROWTH < self.age and self.age < Flower_Stage.SPREADING:
            self.stage = Flower_Stage.GROWTH
        elif Flower_Stage.SPREADING < self.age and self.age < Flower_Stage.DEATH:
            self.stage = Flower_Stage.SPREADING
            seeds = self.calculate_generated_seeds(step_past)
            if seeds == 1: 
                message_status = Game_Message_Status.One_Seed_Generated
                self.stage = Flower_Stage.NULL
            elif seeds == 2:
                self.stage = Flower_Stage.NULL
                message_status = Game_Message_Status.Two_Seed_Generated
        elif Flower_Stage.DEATH < self.age:
            message_status = Game_Message_Status.Flower_Is_Fully_Growed
            self.stage = Flower_Stage.NULL #flower is dead without spreading

        if old_stage != self.stage and self.stage != Flower_Stage.NULL : message_status = Game_Message_Status.New_Flower_Stage
        message1 = self.drowned_and_dried(1.01, 0)
        message2 = self.poisoned(1.01)
        message_status = message1 if message1 is not None else message_status
        message_status = message2 if message2 is not None else message_status

        return message_status

    def drowned_and_dried(self, max, min):
        if self.water_amount > max or self.water_amount < min:
            self.stage = Flower_Stage.NULL
            return Game_Message_Status.Flower_Is_Dead
        return None

    def poisoned(self, max):
        if self.fertilizer_amount > max:
            self.stage = Flower_Stage.NULL
            return Game_Message_Status.Flower_Is_Dead
        return None

    def calculate_generated_seeds(self, time_step):
        average_fertilizer_amount = self.total_fertilizer_amount / self.call_time
        seeds = 0
       
        if time_step > 0.05:
            rate = random.uniform(0.0, 0.8)
            if rate <= average_fertilizer_amount:
                seeds += 1
            rate = random.uniform(0.0, 0.7)
            if rate <= ( average_fertilizer_amount):
                seeds += 1
        
        return seeds

    # --------------- Class -----------------------

class Intent_Name:
    """
    this class is a collection of different intens
    """
    help_intent = "AMAZON.HelpIntent"
    cancel_intent = "AMAZON.CancelIntent"
    stop_intent = "AMAZON.StopIntent"
    fertilize = "FertilizeIntent"
    special_fertilize = "SpecialFertilizeIntent"
    water = "WaterIntent"
    new_game = "NewGameIntent"
    load_game = "LoadGameIntent"
    report = "ReportIntent"
    hint = "HintIntent"
    pour = "PourIntent"
    dig = "DigIntent"
    pause = "AMAZON.PauseIntent"
    check = "CheckScoreIntent"

class GardenError(Exception):
    pass