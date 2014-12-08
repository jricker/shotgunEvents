from shotgun_api3 import Shotgun
import mw_shotgun_keys
import mw_scheduling
sg = Shotgun(mw_shotgun_keys.SERVER_PATH, mw_shotgun_keys.SCRIPT_USER, mw_shotgun_keys.SCRIPT_KEY)
############################################
class Events():
	def __init__(self):
		self.suffix_dict = ''
		self.event_dict = {}
		self.saved_event_data = False
	def distrubute_event(self, event):
		J = self.process_event(event)
		if J['event_type'] == 'Shotgun_Asset_New':
			self.saved_event_data = False
			self.saved_event_data = event
			self.create_group(event_data = J)
		if J['event_type'] == 'Shotgun_Sequence_New':
			print 'new setup sectioned'
			#self.saved_event_data = event
			#if self.saved_event_data:
			#	if self.process_event(self.saved_event_data)['event_type'] == 'Shotgun_Asset_New':
			#		print ' this sequence has been created from an asset creation, move along'
			#	elif self.process_event(self.saved_event_data)['event_type'] == 'Shotgun_Task_New':
			#		print ' task was created, has no effect'
			#	else:
			#		print ' this sequence has been craeted on an already existing asset, adjuste accordingly'
			self.saved_event_data = False
			self.update_tags(event_data = J)
		if J['event_type'] == 'Shotgun_Shot_New':
			self.saved_event_data = False
			self.saved_event_data = J
			self.update_tags(event_data = J)
		if J['event_type'] == 'Shotgun_Task_New':
			self.saved_event_data = event #testing this, remove it everything gets broekn
			self.update_tags(event_data = J)
		if J['event_type'] == 'Shotgun_Asset_Change':
			if J['attribute_name'] == 'sg_asset_type':
				if self.saved_event_data:
					if J['meta_entity_id'] == self.process_event(self.saved_event_data)['meta_entity_id']:
						self.find_asset_template(J)
			elif J['attribute_name'] == 'sequences':
				if self.saved_event_data:
					print ' sequence check active'
					print J['meta_added'] # This is the name of the sequence
					print J['entity_name'] # this is the name of the asset it's attached to
					print J['project_name'] # this is the name of the project
					self.saved_event_data = False
			elif J['attribute_name'] == 'code':
				if 'meta_new_value' in J:
					self.update_tags(event_data = J)
		if J['event_type'] == 'Shotgun_Task_Change':
			user_list = []
			if J['attribute_name'] == 'task_assignees':
				if J['meta_added'] != []:
					for i in J['meta_added']:
						user_list.append(i)
				if J['meta_removed'] != []:
					for i in J['meta_removed']:
						user_list.append(i)
				self.create_schedule(user_list, J['project_id'])
			elif J['attribute_name'] == 'due_date' or J['attribute_name'] == 'start_date':
				task = sg.find_one('Task', filters= [['id', 'is', J['meta_entity_id']]], fields = ['task_assignees'])
				user_list = task['task_assignees']
				self.create_schedule(user_list, J['project_id'])
	def processTags(self, orig_tag_list, tag_to_remove, tag_to_add):
		if tag_to_remove in orig_tag_list:
			new_tag_list = [ x for x in orig_tag_list if x != tag_to_remove ]
			new_tag_list.append(tag_to_add)
			return new_tag_list
	def update_tags(self, event_data):
		if 'meta_new_value' in event_data:
			print 'Asset Name Changed or Added - Updating Tags for shots and sequences'
			proj = sg.find_one('Project', [['name', 'is', event_data['project_name'] ] ], fields = ['name', 'id'])
			shots = sg.find('Shot', filters= [['project', 'is', {'type':'Project', 'id':proj['id']}]], fields = ['code', 'id', 'tag_list'])
			sequences = sg.find('Sequence', filters= [['project', 'is', {'type':'Project', 'id':proj['id']}]], fields = ['code', 'id', 'tag_list'])
			tasks = sg.find('Task', filters= [['project', 'is', {'type':'Project', 'id':proj['id']}]], fields = ['code','id', 'tag_list'])
			for i in shots:
				if event_data['meta_old_value'] in i['tag_list']:
					sg.update('Shot', i['id'], {'tag_list' : self.processTags(i['tag_list'], event_data['meta_old_value'], event_data['meta_new_value']) } )
			for i in sequences:
				if event_data['meta_old_value'] in i['tag_list']:
					sg.update('Sequence', i['id'], {'tag_list' : self.processTags(i['tag_list'], event_data['meta_old_value'], event_data['meta_new_value']) } )
			for i in tasks:
				if event_data['meta_old_value'] in i['tag_list']:
					sg.update('Task', i['id'], {'tag_list' : self.processTags(i['tag_list'], event_data['meta_old_value'], event_data['meta_new_value']) } ) 
		elif event_data['event_type'] == 'Shotgun_Shot_New':
			#print 'Shot Created - Updating Tags'
			# Find the shot via the meta ID. Return ID, CODE, and ASSETS
			shot = sg.find_one('Shot', [['id', 'is', event_data['meta_entity_id']]], fields = ['id', 'code', 'assets'])
			for i in shot['assets']:
				if i['name'] != []:
					tag = i['name']
					sg.update('Shot', shot['id'], {'tag_list' : [tag]} )
			# UPDATE THE TASKS THAT ARE AUTOMATICALLY CREATED FOR THE SHOT
			tasks = sg.find_one('Shot', [['code', 'is', event_data['entity_name']] ] , fields = ['name', 'id', 'tasks'])
		elif event_data['event_type'] == 'Shotgun_Sequence_New':
			#print 'Sequence Created - Updating Tags'
			# Find the shot via the meta ID. Return ID, CODE, and ASSETS
			sequence = sg.find_one('Sequence', [['id', 'is', event_data['meta_entity_id']]], fields = ['id', 'code', 'assets'])
			for i in sequence['assets']:
				if i['name'] != []:
					tag = i['name']
					sg.update('Sequence', sequence['id'], {'tag_list' : [tag]} )
		elif event_data['event_type'] == 'Shotgun_Task_New':
			#print 'Task Created - Updating Tags'
			task = sg.find_one('Task', [['id', 'is', event_data['meta_entity_id']]], fields = ['id','code', 'entity']) # grab the task info
			entity = task['entity'] # get the entity of that task to test if it's an asset or a shot/sequence.
			tag = ''
			if entity['type'] == 'Asset': # see if the task was created on the asset itself
				tag = entity['name']
			else: # this is for if the task is created int he shot or sequence section
				element = sg.find_one(entity['type'], [['id', 'is', entity['id']]], fields = ['assets'])
				X = element['assets']
				if X==[]:
					print 'no asset associated with shot or sequence - FIX THIS'
					tag = 'NONE - FIX THIS!'
				else:
					tag = X[0]['name']
			sg.update('Task', task['id'], {'tag_list' : [tag]} )
			print 'Updated->', '::', entity['name'], ' ', event_data['entity_name'] , '::', tag
	def create_group(self, event_data):
		print 'Creating Group for new asset'
		group_name = event_data['entity_name']
		asset_name = group_name
		user_name = [{'type':'HumanUser','id':60}]
		###########################################
		asset = sg.find_one('Asset', [['code', 'is', asset_name] ], fields = ['code'] )
		asset_code_name = [{'type':'Asset','id':asset['id']}]
		propertyValues = { "code" : group_name, 'users':user_name, 'asset_sg_groups_assets':asset_code_name }
		sg.create('Group', propertyValues )
	def create_schedule(self, user_list, project_id):
		for i in user_list:
			print i
			print i['id']
			mw_scheduling.create_final(i['id'], project_id)
   	def process_asset(self, event_data):
   		print 'placeholder'
	def clean_event(self, event):
		event = dict(event)
		for i in event.keys():
			if type(event[i]) is not dict:
				self.event_dict[self.suffix_dict+i] = event[i]
			else:
				self.suffix_dict = i+'_'
				self.clean_event(event[i])
		self.suffix_dict = ''
		return self.event_dict
	def process_event(self, event):
		data = self.clean_event(event)
		self.suffix_dict = ''; self.event_dict = {} # reset the event_dict and suffix_dict for next event process
		return data
	def isolate_event(self, event_data, action_item):
		if action_item in event_data:
			value = event_data[action_item]
			return value
	def create_padding(self, data = None, amount = 2):
		pad = '0'*amount
		iteratorPadding = (pad[:len(pad)-len(str(data))] + str(int(data) ) )
		return iteratorPadding
	def create_sequence(self, sequence_name, project, asset ):
		#sequence = sg.create('Sequence', {'code':sequence_name,'project':project, 'assets':asset} )
		print 'testing this sequence create area'
		#sg.update('Sequence', sequence['id'], {'sg_sequence':sequence} )
		#print 'creating sequence --> ', shot_name
	def create_shot(self, shot_name, shot_type, sequence, project, asset ):
		shot = sg.create('Shot', {'code':shot_name, 'task_template':shot_type, 'sg_sequence':sequence , 'project':project, 'assets':asset} )
		sg.update('Shot', shot['id'], {'sg_sequence':sequence} )
		sg.update('Shot', shot['id'], {'sg_shot_category':self.check_shot_type(shot_type['name'])} )
		print 'creating shot --> ', shot_name
	def check_shot_type(self, shot_type):
		X = 'na'
		if shot_type == 'Mograph Shots':
			X = 'mogrph'
		elif shot_type == 'Cinematic Shots':
			X = 'cinem'
		elif shot_type == 'Editing Shots':
			X = 'edit'
		elif shot_type == 'Gameplay Shots':
			X = 'gmp'
		elif shot_type == 'LiveAction Shots':
			X = 'live'
		return X 
	def create_cinematic(self, event_data = {}, asset_id = None, project_id = None, sequence_count = 3, shots_per_sequence = 8):
		#print 'creating CINEMATIC'
		for i in range(sequence_count):
			count = self.create_padding(data = 1+i, amount = 2) # add in the +1 on top so sc starts at 01
			asset = sg.find_one('Asset', [['id', 'is', asset_id]] ,fields = ['code'])
			sequence_name = asset['code']+'_sc' + count
			print asset
			print sequence_name
			#print sequence_name, ' -->', ' this is sequence_name'
			#print asset_name, '-->', 'this is asset_name'
			project = sg.find_one('Project', [['id', 'is', project_id]] )
			#print sequence_name
			#asset = sg.find_one('Asset', [['code', 'is', asset_name]], fields = ['project','id'])
			#asset_main = sg.find_one('Asset', [['id', 'is', asset['id']]])
			#project =  asset['project']#, ' THIS SHOULD BE THE PROJECT'
			sequence = sg.create('Sequence', {'code':sequence_name, 'project':project, 'assets':[asset]} )
			#print sequence['id']
			#sg.create('Sequence', {'code':sequence_name, 'asset':asset_name} )
			for x in range(shots_per_sequence):
				padding = self.create_padding(data = 10+x*10, amount= 3)
				shot_name = sequence_name + '_sh'+ padding
				#print shot_name, ' -->', ' this is shot_name'
				self.create_shot(
					shot_name = shot_name, 
					shot_type = {'type':'TaskTemplate','id': 15 ,'name': 'Cinematic Shots'}, 
					sequence = sequence, 
					project = project,
					asset = [asset]
					)
		self.saved_event_data = False # reset data
	def create_cinematic_trailer(self, event_data = {}, asset_id = None, project_id = None, sequence_count = 5, shots_per_sequence = 8):
		for i in range(sequence_count):
			count = self.create_padding(data = 1+i, amount = 2) # add in the +1 on top so sc starts at 01
			asset = sg.find_one('Asset', [['id', 'is', asset_id]] ,fields = ['code'])
			sequence_name = asset['code']+'_sc' + count
			project = sg.find_one('Project', [['id', 'is', project_id]] )
			sequence = sg.create('Sequence', {'code':sequence_name, 'project':project, 'assets':[asset]} )
			for x in range(shots_per_sequence):
				padding = self.create_padding(data = 10+x*10, amount= 3)
				shot_name = sequence_name + '_sh'+ padding
				self.create_shot(
					shot_name = shot_name, 
					shot_type = {'type':'TaskTemplate','id': 15 ,'name': 'Cinematic Shots'}, 
					sequence = sequence, 
					project = project,
					asset = [asset]
					)
		self.saved_event_data = False # reset data
	def create_dev_diary(self, event_data = {}, asset_id = None, project_id = None, sequence_count = 2, shots_per_sequence = 1):
		for i in range(sequence_count):
			count = self.create_padding(data = 1+i, amount = 2) # add in the +1 on top so sc starts at 01
			asset = sg.find_one('Asset', [['id', 'is', asset_id]] ,fields = ['code'])
			if i+1 == 1:
				sequence_name = asset['code']+'_sc' + count
				shot_type = 'Cinematic Shots'
				shot_type_id = 15
			elif i+1 ==2:
				sequence_name = asset['code']+'_sc' + count
				shot_type = 'Mograph Shots'
				shot_type_id = 20
			else:
				shot_type = 'Cinematic Shots'
				shot_type_id = 15
			project = sg.find_one('Project', [['id', 'is', project_id]] )
			sequence = sg.create('Sequence', {'code':sequence_name, 'project':project, 'assets':[asset]} )
			for x in range(shots_per_sequence):
				padding = self.create_padding(data = 10+x*10, amount= 3)
				shot_name = sequence_name + '_sh'+ padding
				self.create_shot(
					shot_name = shot_name, 
					shot_type = {'type':'TaskTemplate','id': shot_type_id ,'name': shot_type}, 
					sequence = sequence,
					project = project,
					asset = [asset]
					)
		self.saved_event_data = False # reset data
	def create_screenshot(self, event_data, asset_name):
		print 'creating SCREENSHOTS'
		self.saved_event_data = False
	def create_TVC(self, event_data, asset_name):
		print 'creating TVC'
		self.saved_event_data = False
	def create_walkthrough(self, event_data, asset_name):
		print 'creating WALKTHROUGH'
		self.saved_event_data = False
	def create_insider_access(self, event_data, asset_name):
		print 'creating INSIDER ACCESS'
		self.saved_event_data = False
	def find_asset_template(self, event_data):
		asset_type = event_data['meta_new_value']
		asset = sg.find_one('Asset', [['id', 'is', event_data['meta_entity_id']] ], fields = ['code', 'sg_create_default'])
		default = asset['sg_create_default']
		project_id = event_data['project_id']
		asset_id = asset['id']
		if default == 'y':
			if asset_type == 'Cinematic':
				self.create_cinematic(event_data, asset_id, project_id)
			elif asset_type == 'Cinematic Trailer':
				self.create_cinematic_trailer(event_data, asset_id, project_id)
			elif asset_type == 'Developer Diary':
				self.create_dev_diary(event_data, asset_id, project_id)
			###################################################elif asset_type == 'Insider Access':
			###################################################	self.create_insider_access(event_data, asset_name)
			###################################################elif asset_type == 'Walkthrough':
			###################################################	self.create_walkthrough(event_data, asset_name)
			###################################################elif asset_type == 'TVC':
			###################################################	self.create_TVC(event_data, asset_name)
			###################################################elif asset_type == 'Screenshots':
			###################################################	self.create_screenshot(event_data, asset_name)
#	def find_sequence_template(self, event_data):
#		asset_type = event_data['meta_new_value']
#		asset = sg.find_one('Asset', [['id', 'is', event_data['meta_entity_id']] ], fields = ['code'])
#		asset_name = asset['code']
#if __name__ == '__main__':	
#	mw = Events()
#	event = {'asset_name':'test'}
#	mw.create_cinematic(event, 'test')
	#event_data = mw.process_event(event)