keys = []
values = []
def find_keys(dictionary):
    for key, value in dictionary.iteritems():
        if type(value) is dict:
            find_keys(value)
        else:
            keys.append(key); values.append(value)
    return dict(zip(keys,values))
def check_change(sg, logger, event, args):
    print '!!!!!!!!!!!!!!!!!!!!'
    print find_keys(dict(event))
    print '!!!!!!!!!!!!!!!!!!!!'
    meta = event['meta']
    project = event['project']
    if event != None:
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
    	            users = []
    	            for i in task['task_assignees']:
    	                users.append(i['id'])
    	            return 'task_updated', users, project['id']
    	elif event['attribute_name'] == None:
			if event['event_type'] == 'Shotgun_Asset_New':
				return 'new_asset', 'placeholder'