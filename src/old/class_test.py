class MW_Events():
	def __init__(self):
		self.suffix_dict = ''
		self.event_dict = {}
		self.saved_event_data = False
	def cleanEvent(self, event):
		event = dict(event)
		for i in event.keys():
			if type(event[i]) is not dict:
				self.event_dict[self.suffix_dict+i] = event[i]
			else:
				self.suffix_dict = i+'_'
				self.cleanEvent(event[i])
		self.suffix_dict = ''
		return self.event_dict
	def processEvent(self, event):
		data = self.cleanEvent(event)
		self.suffix_dict = ''; self.event_dict = {} # reset the event_dict and suffix_dict for next event process
		return data
	def isolateEvent(self, event_data, action_item):
		if action_item in event_data:
			value = event_data[action_item]
			return value

if __name__ == '__main__':	
	mw = MW_Events()
	event_data = mw.processEvent(event)
	event_type = mw.isolateEvent(event_data, 'event_type')
	if event_type == 'Shotgun_Booking_Retirement':
		print ' this is a booking delete event'
	elif event_type == 'Create_Asset_New':
		mw.saved_event_data = event_data
		print ' a new asset has been created'
	elif event_type == 'Asset_Attribute_Change':
		if mw.saved_event_data:
			print ' a change has occured on a newly created asset'
			"""
			!! action placed here !!
			# we use this section to check the events, see if they are a change in the video type
			# if they are, then refer back to the saved event data, see if it has the create default
			# button checked on during creation. If so, then go forward and populate that asset
			# with the default shots and related sequences for easy generic production
			# ONCE finished processing, then reset the saved event data back to 0.
			"""
			mw.saved_event_data = False # reset the saved event to nothing
		else:
			print ' a change has just occured in the asset'
	#print B
