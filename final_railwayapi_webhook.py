# importing packeges

from flask import Flask
from flask import request
from flask import make_response
from datetime import date
import json
import requests

#system date for canceled train checking
datetime=date.today()
d1=datetime.today().strftime('%Y-%m-%d')
d1=d1.replace("-","")
apikey="9d2827552d66c0b90be49da847ab92f3"

#flask set up
app = Flask(__name__)

#handling the webhook request
@app.route('/webhook', methods=["GET","POST"])
def webhook():

    #getting the request from dialogflow
    req = request.get_json(silent=True, force=True)
    #print(json.dumps(req,indent=4))

    #getting the intent name
    intent_name = req["queryResult"]["intent"]["displayName"]

    #handling the get Train_Info intent
    if(intent_name == 'train_info'):
        return Train_Info(req)
    #handling the get Train_Status intent
    if(intent_name == 'train_status'):
        return trainstatus(req)
    #handling the get Canceled_Train intent
    if(intent_name == 'Canceled_trains'):
        return cancel(req)
    #handling the get Book_Ticket intent
    if(intent_name == 'book_Ticket'):
        return SeatAvailability(req)
    # returning response
    
# Train info function
def Train_Info(data):
 
    # getting tain number
    trainnumber=int(data["queryResult"]["parameters"]["number"][0])
    trainnumber=str(trainnumber)
    # print(trainnumber)
    
    # requesting the api
    nourl='http://indianrailapi.com/api/v2/TrainInformation/apikey/'+apikey+'/TrainNumber/'
    finalurl=nourl+trainnumber+'/'
    obj=requests.get(finalurl).json()

    # fetching data from json and check the response code
    if(obj['ResponseCode']=='200'):
        result="Your train number : "+ trainnumber +"  "+obj['TrainName']+" " + " from the source "+ obj['Source']['Code'] +" of time "+ obj['Source']['Arrival'] +" and arrive at the station " + obj['Destination']['Code'] +" of time "+ obj['Destination']['Arrival']
        print(result)

        # returning the response
        return {
            "fulfillmentText": result
        }

    # handiling error
    elif obj['ResponseCode']!='200' : 
        return try_error(obj['ResponseCode'])

#  Train status method
def trainstatus(data):
    # getting train number
    trainnumber=int(data["queryResult"]["parameters"]["number"][0])
    trainnumber=str(trainnumber)

    # request the train status api
    url='http://indianrailapi.com/api/v2/livetrainstatus/apikey/'+apikey+'/trainnumber/'
    finalurl=url+trainnumber+'/date/'+d1+'/'
    obj=requests.get(finalurl).json()
    
    # fetch the data from the json 
    if(obj['ResponseCode']=='200'):
        result="your Train number "+ trainnumber
        for x in obj['TrainRoute']:
            result=result+"\nStation name           :"+x['StationName']+"\n Schedule arrival time   :"+x['ScheduleArrival']+"\n schedule depature time : "+x['ScheduleDeparture']+ "\n\n "
        print(result)

        # returning the response
        return {
            "fulfillmentText": result
        }
    
    # handiling the error
    elif obj['ResponseCode']!='200': 
        return try_error(obj['ResponseCode'])

# canceled train method  
def cancel(data):

    # request the canceled train api
    cancelurl='https://indianrailapi.com/api/v2/CancelledTrains/apikey/'+apikey+'/Date/'+d1
    can=requests.get(cancelurl).json()  
    print(can)

    # fetching data from the json
    result="Today "+can['TotalTrain']+" Trains are canceled"
    print(result)

    # returning the response
    return {
        "fulfillmentText": result
    }

# booking the train method 
def SeatAvailability(data):

    # getting the train number and changed into string
    trainnumber=int(data['queryResult']['parameters']['number'][0])
    trainnumber=str(trainnumber)

    # getting the class type
    classop=data['queryResult']['parameters']['ClassName'][0]
    classop=str(classop)

    # getting the date
    date=data['queryResult']['parameters']['date']
    date=date[0].replace("-","")
    date=date[0:8]

    # getting the source Station_name and convert it into station code
    fromc=Stationcode[data['queryResult']['parameters']['source'][0].lower()]
    
    # getting the  destination  station name and convert it into station code
    toc=Stationcode[data['queryResult']['parameters']['destination'][0].lower()]
    
    # interactive text
    result = "Checking seat availability for the train number : "+ trainnumber +" on the date of "+date+ " from the station code : "+fromc+" to the station code : "+toc+" the availability seats are \n"

    # requesting seatavailability api
    url='https://indianrailapi.com/api/v2/SeatAvailability/apikey/'+apikey+'/TrainNumber/'+trainnumber+'/From/'+fromc+'/To/'+toc+'/Date/'+date+'/Quota/GN/Class/'+classop
    obj=requests.get(url).json()


    # fetching data from the json
    if obj['ResponseCode']=='200' :

        for x in obj['Availability']:
            result=result+" date on : "+ x['JourneyDate']+" The availability of seats are : "+x['Availability']+" conifirmation percentage: "+x['Confirm']

        # requesting fare api to get the cost for the seat
        fare='http://indianrailapi.com/api/v2/TrainFare/apikey/'+apikey+'/TrainNumber/'+trainnumber+'/From/'+fromc+'/To/'+toc+'/Quota/GN/CK'
        obj1=requests.get(fare).json()
        for f in obj1['Fares']:
            if f['code']== classop:
                rupee=f['Fare']
                result=result+" \n Fare for ur class type is Rs."+rupee+" are u sure to book the ticket"
                # returning the response
                return{
                        'fulfillmentText': result
                    }
    
    # error handling
    elif obj['ResponseCode']!='200' : 
        return try_error(obj['ResponseCode'])

# method for handiling error
def try_error(code):
    if code == '204':

        return {
            "fulfillmentText":'Not able to fetch required data or there is no data for your query!'
        }
    if code == '201':
        return {
            "fulfillmentText":"Invalid details. Please enter Valid details"
        }
      
    elif code == '210':
        return {
            "fulfillmentText":"Train doesn’t run on the date queried!"
        }
      
    elif code == '220':
        return {
            "fulfillmentText":'Flushed PNR!'
        }

    elif code == '221':
        return {
            "fulfillmentText":'Invalid PNR supplied!',
        }

    elif code == '304':
        return {
            "fulfillmentText":'Data couldn’t be fetched. No data available for the given query!'
        }

    elif code == '404':
        return {
            "fulfillmentText":"Sorry, Doesn't Exist! :/"
        }

    elif code == '405':
        return {
            "fulfillmentText":"Data couldn’t be loaded! Request didn't go through."
        }

    elif code == '500':
        return {
            "fulfillmentText":'Sorry! Unable to process request at this time! Railway API Error Code: 500'
        }

    else :
        return {
            "fulfillmentText":'Sorry! please try again'
        }
        
# dictionary for user input station name to station code
Stationcode={"andevnagar":"ACND","abhaipur":"AHA","abhayapuriasam":"AYU","abohar":"ABS","aburoad":"ABR","achalda":"ULD","achhnera Junction":"AH","achhnera":"AH","adasroad":"ADD",
'adavali':"ADVI",'adesar':'AAR','adgaonbuzurg':'ABZ','adhartal':'ADTL','adhikari':'ADQ','adisaptagram':'ADST','adilabad':'ADB','adina':'ADF','adipur':'AI','adityapur':'ADTP',
'adoni':'AD','adrajunction':'ADRA','adra':'ADRA','adra':'ADRA','adrshngrdelhi':'ANDI','delhi':'ANDI','aduturai':'ADT','agartala':'AGTL','agasod':'AGD','aghwanpur':'AWP','agomoni':'AGMN','agorikhas':'AGY',
'agracantt':'AGC','agra':'AGC','agracity':'AGA','agrafort':'AF','ahmedabadjunction':'ADI','ahmedabad':'ADI','ahmedabadmg':'ADIJ','aluva':'AWY','anandvihar':'ANVR','anandvihartrm':'ANVT',
'anandapuram':'ANF','bangalorecant':'BNC','bangalorecyjunction':'SBC','bengaluru':'SBC','bangaloreeast':'BNCE','bilaspurjunction':'BSP','bilaspurroad':'BLOR','bilaspurroad':'BLQR',
'chandigarh':'CDG','chengalpattu':'CGL','chengannur':'CNGR','chennaibeach':'MSB','chennaicentral':'MAS','chennaiegmore': 'MS','chinnasalem':'CHSM','salem':'CHSM','coimbatorejunction':'CBE',
'coimbatore':'CBE','coimbatorenrth':'CBF','durgapur':'DGR','durgapura':'DPA','eranakulamjunction':'ERS','eranakulam':'ERS','ernakulamtown':'ERN','erodejunction': 'ED','erode': 'ED','garhjaipur': 'GUG',
'jamjodhpurjunction': 'JDH','jamjodhpur': 'JDH','jammu Tawi': 'JAT','jolarpettai':'JTJ','kannur': 'CAN','khammam':'KMT','kolkata':'CP','kolkata': 'KOAA','kollamjunction':'QLN','kollam':'QLN',
'kottayam': 'KTYM','kozhikode': 'CLT','maduraijunction':'MDU','madurai':'MDU','mumbaicentral':'BCT','mumbai':'BCT','mumbaicst':'CSTM','nagpur':'NGP','nagpurroad':'NPRD','palakkad':'PGT','Palani': 'PLNI',
'puducherry':'PDY','pudukkottai':'PDKT','punejunction': 'PUNE','pune': 'PUNE','rajkotjunction':'RJT','rajkot':'RJT','thiruvarurjunction':'TVR','thiruvarurjunction':'TVR','thrisur':'TCR','tirupati':'TPTY',
'tiruppur':'TUP','vijayawadajunction':'BZA','vijayawada':'BZA','villuparamjunction':'VM','villuparam':'VM','Villuppuram':'VM','viluppuram': 'VM'}


if __name__ == '__main__':
    app.run()
