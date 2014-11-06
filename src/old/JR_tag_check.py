#########################################################################################################################
def registerCallbacks(reg):
    """Register all necessary or appropriate callbacks for this plugin."""
    scriptName = ''
    scriptKey = ''
    # Callbacks are called in registration order.
    reg.registerCallback(scriptName, scriptKey, createTags)
def processTags(orig_tag_list, tag_to_remove, tag_to_add):
	if tag_to_remove in orig_tag_list:
		new_tag_list = [ x for x in orig_tag_list if x != tag_to_remove ]
		new_tag_list.append(tag_to_add)
		return new_tag_list
def createTags(sg, logger, event, args):
    meta = event['meta']
    entity = event['entity']
    print '#########################  CHECKING FOR CHANGES  ##################################'
    if event['attribute_name'] == 'code':
		if event['event_type'] == 'Shotgun_Asset_Change':
			if meta['type'] == 'attribute_change':
				if 'new_value' in meta:
					print 'ASSET NAME CHANGE  ##################################'
					proj = event['project'] #sg.find_one('Project', [['name', 'is', 'Hardline'] ], fields = ['name', 'id'])
					shots = sg.find('Shot', filters= [['project', 'is', {'type':'Project', 'id':proj['id']}]], fields = ['code', 'id', 'tag_list'])
					sequences = sg.find('Sequence', filters= [['project', 'is', {'type':'Project', 'id':proj['id']}]], fields = ['code', 'id', 'tag_list'])
					tasks = sg.find('Task', filters= [['project', 'is', {'type':'Project', 'id':proj['id']}]], fields = ['code','id', 'tag_list'])
    				for i in shots:
    					if meta['old_value'] in i['tag_list']:
    						sg.update('Shot', i['id'], {'tag_list' : processTags(i['tag_list'], meta['old_value'], meta['new_value']) } )
    				for i in sequences:
    					if meta['old_value'] in i['tag_list']:
    						sg.update('Sequence', i['id'], {'tag_list' : processTags(i['tag_list'], meta['old_value'], meta['new_value']) } )
    				for i in tasks:
    					if meta['old_value'] in i['tag_list']:
    						sg.update('Task', i['id'], {'tag_list' : processTags(i['tag_list'], meta['old_value'], meta['new_value']) } ) 
    elif event['attribute_name'] == None:
    	if event['event_type'] == 'Shotgun_Shot_New':
    		print 'SHOT CREATED  ##################################'
    		# Find the shot via the meta ID. Return ID, CODE, and ASSETS
    		shot = sg.find_one('Shot', [['id', 'is', meta['entity_id']]], fields = ['id', 'code', 'assets'])
    		for i in shot['assets']:
    			if i['name'] != []:
    				tag = i['name']
    				sg.update('Shot', shot['id'], {'tag_list' : [tag]} )
    		# UPDATE THE TASKS THAT ARE AUTOMATICALLY CREATED FOR THE SHOT
    		tasks = sg.find_one('Shot', [['code', 'is', entity['name']] ] , fields = ['name', 'id', 'tasks'])
    		for i in tasks['tasks']:
    		    sg.update('Task', i['id'], {'tag_list' : [tag]} )
    	elif event['event_type'] == 'Shotgun_Sequence_New':
    		print 'SEQUENCE CREATED  ##################################'
    		# Find the shot via the meta ID. Return ID, CODE, and ASSETS
    		sequence = sg.find_one('Sequence', [['id', 'is', meta['entity_id']]], fields = ['id', 'code', 'assets'])
    		for i in sequence['assets']:
    			if i['name'] != []:
    				tag = i['name']
    				sg.update('Sequence', sequence['id'], {'tag_list' : [tag]} )
    	elif event['event_type'] == 'Shotgun_Task_New':
    		print 'TASK CREATED  ##################################'
    		# Find the shot via the meta ID. Return ID, CODE, and ASSETS
    		task = sg.find_one('Task', [['id', 'is', meta['entity_id']]], fields = ['id','code','entity.Shot.assets'])
    		for i in task['entity.Shot.assets']:
    			print i
    			if i['name'] != []:
    				tag = i['name']
    				sg.update('Task', task['id'], {'tag_list' : [tag]} )
#########################################################################################################################

