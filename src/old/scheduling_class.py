from shotgun_api3 import Shotgun
from datetime import date, timedelta as td
import calendar
#########################################################################################################################
#########################################################################################################################
SERVER_PATH = '' # change this to https if your studio uses SSL
SCRIPT_USER = ''
SCRIPT_KEY = ''
sg = Shotgun(SERVER_PATH, SCRIPT_USER, SCRIPT_KEY)
#########################################################################################################################
def registerCallbacks(reg):
    """Register all necessary or appropriate callbacks for this plugin."""
    scriptName = ''
    scriptKey = ''
    # Callbacks are called in registration order.
    reg.registerCallback(scriptName, scriptKey, process_change)
#########################  CHECKING FOR SCHEDULE  ##################################
def process_change(sg, logger, event, args):
    action = CC.check_change(sg, logger, event, args)
    if action == None:
        pass
    else:
        if action[0] == 'task_reassigned':
            print action, '    THIS IS RE-ASSIGNED'
            for i in action[1]:
                print i,' HERE WE AREEEEEEEE'
                CC.create_final(i, action[2])
        elif action[0] == 'task_updated':
            print action, '    THIS IS UPDATED'
            CC.create_final(action[1], action[2])
class Schedule():
    def __init__(self):
        self.user_list = []
    def check_change(self, sg, logger, event, args):
        meta = event['meta']
        project = event['project']
        if event['attribute_name'] == 'task_assignees':
            if event['event_type'] == 'Shotgun_Task_Change':
                added = meta['added']; removed = meta['removed']
                users = []
                try:
                    for i in added:
                        users.append(i['id'])
                except IndexError:
                    pass
                try:
                    for i in removed:
                        users.append(i['id'])
                except IndexError:
                    pass
                return 'task_reassigned', users, project['id']
        elif event['attribute_name'] == 'start_date' or event['attribute_name'] == 'due_date':# or event['attribute_name'] == 'start_date' or event['attribute_name'] == 'due_date':
            if event['event_type'] == 'Shotgun_Task_Change':
                if meta['type'] == 'attribute_change':
                    task = sg.find_one('Task', filters= [['id', 'is', meta['entity_id']]], fields = ['task_assignees'])
                    user = task['task_assignees'][0]
                    return 'task_updated', user['id'], project['id']
        else:
            pass
    def clean_dates(self, dates):
        try:
            X = dates.split('-')
            formated_date = date(int(X[0]),int(X[1]),int(X[2]))
        except AttributeError: # this means it's already a date format
            formated_date = dates
        return formated_date
    def remove_booking(self, ID):
        if isinstance(ID, list):
            for i in ID:
                sg.delete('Booking', i )
        else:
            sg.delete('Booking', ID)
    def create_booking(self, user_id, project_id, start_date, end_date):
        project = sg.find_one('Project', [['id', 'is', project_id] ], fields = ['name', 'id'])
        values = { "project" : project, 'user':{'type':'HumanUser','id':user_id}, 'start_date':start_date, 'end_date':end_date }
        sg.create('Booking', values)
    def get_bookings(self, user_id, project_id, start_date, end_date):
        booking = sg.find('Booking', filters= [['user', 'is', {'type':'HumanUser', 'id':user_id}]], fields = ['project', 'id', 'start_date', 'end_date' ])
        current_bookings = [] 
        overlap_bookings = []
        #
        time_between_tasks = self.process_dates(str(start_date), str(end_date))
        for i in booking:
            ID = i['id']
            start_date = self.clean_dates(i['start_date'])
            end_date = self.clean_dates(i['end_date'])
            current_bookings.append([{'start_date':start_date, 'end_date':end_date, 'id':ID}])
        T = []
        for i in current_bookings:
            delta = i[0]['end_date'] - i[0]['start_date']
            T.append({'id':i[0]['id'],'dates':[i[0]['start_date'] + td(days=x) for x in range(delta.days + 1)]})
        for i in T:
            for x in time_between_tasks:
                if x in i['dates']:
                    overlap_bookings.append(i['id'])
        return booking, list((set(overlap_bookings)))
    ##############################################################################################
    def get_all_tasks(self, project_id, user_id):
        task_list = []
        all_tasks = sg.find('Task', filters= [['project', 'is', {'type':'Project', 'id':project_id}]], fields = ['content', 'id', 'start_date', 'due_date', 'task_assignees'])
        for i in all_tasks:
            user =  i['task_assignees']
            if user != []:
                if user[0]['id'] == user_id:
                    if i['start_date'] == None:
                        pass
                    elif i['due_date'] == None:
                        pass
                    else:
                        task_list.append([i['start_date'], i['due_date']])
        return task_list
    def test(self):
        pass
    def process_dates(self, start_date, end_date):
        X = []
        start = self.clean_dates(start_date)
        end = self.clean_dates(end_date)
        delta = td(days=1)
        d = start
        while d <= end:
            X.append(d)
            d += delta
        return X
    def find_hole(self, user_id, project_id):
        X = []
        Y = []
        A = []
        find = []
        for i in self.get_all_tasks(project_id, user_id):
            X.append(i)
        for i in X:
            for x in i:
                find.append(x)
        set_find_early = set(find)
        temp_find_early = list(set_find_early)
        clean_find_early = sorted(temp_find_early)
        start_time = clean_find_early[0]
        end_time = clean_find_early[-1]
        for i in X:
            Y.append( self.process_dates(i[0], i[1]) )
        for i in Y:
            for x in i:
                A.append(x)
        test = A
        start = self.clean_dates(start_time)
        end = self.clean_dates(end_time)
        delta = td(days=1)
        d = start
        diff = 0
        weekend = set([5, 6])
        while d <= end:
            if d.weekday() not in weekend:
                diff += 1
            else:
                if d.weekday() == 5:
                    if d-delta in test or d+delta+delta in test:
                        A.append(d)
                elif d.weekday() == 6:
                    if d-delta-delta in test or d+delta in test: #check back and forth twice depending on the day, sat or sunday. for A link
                        A.append(d)
            d += delta
        temp = set(A)
        all_dates_clean = list(temp)
        full_dates = sorted(all_dates_clean)
        holed_days = self.count_days(full_dates)
        return holed_days, full_dates
    def find_last_day(self, year_id, month_id):
        last_day = calendar.monthrange(year_id,month_id)[1]
        return last_day
    def count_days(self, date_list):
        X = []
        Y = []
        for i in range(len(date_list)):
            delta = td(days=1)
            next_day = delta # must assign next_day before using
            day = int(str(date_list[0]).split('-')[2])
            month = int(str(date_list[0]).split('-')[1])
            year = int(str(date_list[0]).split('-')[0])
            last_day = calendar.monthrange(year, month)[1]
            if day == last_day:
                next_day = date(year, month+1, 01)
            else:
                next_day= date_list[i]+delta
            if next_day not in date_list:
                if i+1 != len(date_list):
                    X.append([next_day, date_list[i+1] ])
        beginning = date_list[0]
        end = date_list[-1]
        end_plus_one = self.clean_dates(end) + delta
        if X == []:
            Y.append( self.process_dates(str(beginning), str(end_plus_one) ) )
        elif len(X) == 1:
            Y.append( self.process_dates(str(beginning), str(X[0][0]-delta) ) )
            Y.append( self.process_dates(str(X[0][1]), str(end_plus_one) ) )
        elif len(X) > 1:
            BB = len(X)+1
            for i in range(BB):
                if i == 0:
                    Y.append( self.process_dates(str(beginning), str(X[i][0]-delta) ) )
                elif i == BB-1:
                    Y.append( self.process_dates(str(X[i-1][1]), str(end_plus_one) ) )
                else:
                    Y.append( self.process_dates(str(X[i-1][1]), str(X[i][0]-delta) ) )
        return X, Y
    def return_booking(self, ID):
        booking = sg.find('Booking', filters= [['id', 'is', ID]], fields = ['project', 'id', 'start_date', 'end_date' ])
        return booking
    def adjust_booking(self, ID, start_date, end_date):
        pass
    def create_final(self, user_id, project_id):
        for i in range(5):
            print 'adjusting schedule'
        dates = self.find_hole(user_id, project_id)[0][1]
        ##############################################################################################
        bookings = self.get_bookings(user_id, project_id, dates[0][0], dates[-1][-1])
        users_bookings = bookings[0]
        all_overlap_bookings = bookings[1]
        overlap_bookings = []
        for i in all_overlap_bookings:
            booking = self.return_booking(i)
            project = booking[0]['project']
            if project == None:  # this means it's a vacation booking
                pass
            elif project['id'] != project_id:
                pass
            else:
                overlap_bookings.append(i)
        old_bookings = []
        for i in users_bookings:
            ID = i['id']
            project = i['project']
            if project == None: # this means it's a vacation booking
                pass
            elif project['id'] != project_id:
                pass
            else:
                if ID not in overlap_bookings:
                    old_bookings.append(ID)
        self.remove_booking(old_bookings)
        if len(overlap_bookings) == len(dates):
            print ' they have the same amount, adjust accordingly'
            for i in range(len(overlap_bookings)):
                booking = self.return_booking(overlap_bookings[i])
                sg.update('Booking', booking[0]['id'], {'start_date' : dates[i][0], 'end_date':dates[i][-1]} )
        elif len(overlap_bookings) > len(dates):
            print ' theres more bookings than tasks, delete over thel negth of tasks and adjust the rest '
            diff = len(overlap_bookings) - len(dates)
            self.remove_booking(overlap_bookings[diff:])
            for i in range(diff):
                booking = self.return_booking(overlap_bookings[i])
                sg.update('Booking', booking[0]['id'], {'start_date' : dates[i][0], 'end_date':dates[i][-1]} )
        elif len(overlap_bookings) < len(dates):
            print 'adjust as many dates as you can and then create new ones'
            for i in range(len(dates)):
                if i == len(overlap_bookings)-1:
                    booking = self.return_booking(overlap_bookings[i])
                    sg.update('Booking', booking[0]['id'], {'start_date' : dates[i][0], 'end_date':dates[i][-1]} )
                    #print overlap_bookings[i], ' adjust to these dates', dates[i]
                elif i >= len(overlap_bookings):
                    self.create_booking(user_id, project_id, dates[i][0], dates[i][-1])               
                    #print ' create a new booking with these dates', dates[i]
                else:
                    booking = self.return_booking(overlap_bookings[i])
                    sg.update('Booking', booking[0]['id'], {'start_date' : dates[i][0], 'end_date':dates[i][-1]} )
                    #print overlap_bookings[i], ' adjust to these dates', dates[i]
        elif len(overlap_bookings) == 0:
            print 'no bookings currently exist. create new ones.'
            for i in dates:
                self.create_booking(user_id, project_id, i[0], i[-1])
    ##############################################################################################
CC = Schedule()