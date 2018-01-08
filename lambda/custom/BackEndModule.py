import GameModule as gm

class Back_End:
    def __init__(self):
        self.game = gm.Game()
    # --------------- Main handler ------------------

    def lambda_handler(self, event, context):
        
        intent_type = event["request"]["type"]
        
        intent = event["request"]["intent"] if 'intent' in event['request'] else None
        session = event["session"]
        try:
            if event['session']['application']['applicationId'] != "amzn1.ask.skill.4b15972d-e9b6-444e-bb9f-fbec1eee56c7":
                raise ValueError("Invalid Application ID")
            print(str(session['user']['userId']).encode('utf-8'))
            if intent_type == "LaunchRequest": return self.game.launch(intent, session)
            elif intent_type == "IntentRequest": return self.game.update(intent, session)
            elif intent_type == "SessionEndedRequest" : 
                
                if event['request']['reason'] == 'USER_INITIATED':
                    return self.game.end(intent, session, True, False)
            else:
                return self.game.unrecognized_reuqest()
        except Exception as e:
            print(e)
            return self.game.get_error()

BACK_END = Back_End()

def lambda_handler(event, context):
    
    response = BACK_END.lambda_handler(event, context)
    
    return response
        