"""
Extension classes enhance TouchDesigner components with python. An
extension is accessed via ext.ExtensionClassName from any operator
within the extended component. If the extension is promoted via its
Promote Extension parameter, all its attributes with capitalized names
can be accessed externally, e.g. op('yourComp').PromotedFunction().

Help: search "Extensions" in wiki
"""

from TDStoreTools import StorageManager
import TDFunctions as TDF
from packaging import version
from datetime import datetime

class RoomExt:
	"""
	RoomExt description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.Logger = op('logger')

		"""
		A reference to the signalingClient COMP the Room COMP is relying on.
		"""
		TDF.createProperty(
			self,
			'SignalingClient',
			value=self.ownerComp.par.Signalingclient.eval(),
			dependable=True,
			readOnly=False
		)

		self.signalingCheckTimer = op('timer1')

		self.messagesMetadata = {
			'apiVersion': self.ownerComp.par.Signalingapiversion.eval(),
			'compVersion': self.ownerComp.par.Version.eval(),
			'compOrigin': self.ownerComp.path,
			'projectName': project.name,
		}

		"""
		A reference DAT to save our messages to.
		"""
		self.ChatDAT = op('chat')
		self.ChatDAT.clear(keepFirstRow=True)

		"""
		A list of message types used for Room specific signaling. Those types
		are passed when the Room COMP is subscribing to the signalingClient
		COMP.
		"""
		TDF.createProperty(
			self,
			'SignalingClientMessagesTypes',
			value=['Newchat'],
			dependable=True,
			readOnly=False
		)

		self.Subscribe()
		self.signalingCheckTimer.par.start.pulse()

	def OnMessageReceived(self, message: dict) -> None:
		# The following JSON keys are informations about the Signaling protocol
		# and are mandatory
		metadata = message.get('metadata', None)

		if not metadata:
			self.Logger.Error(
				f'The metadata could not be found. Invalid signaling format message. Aborting')
			return

		apiVersion = metadata.get('apiVersion', None)
		compVersion = metadata.get('compVersion', None)
		compOrigin = metadata.get('compOrigin', None)
		projectName = metadata.get('projectName', None)

		sender = message.get('sender', None)

		if not self.isVersionMatching(apiVersion):
			return
		else:
			self.Logger.Info(f'Message received from {sender}:{projectName}:{compOrigin}')

		signalingType = message.get('signalingType', '')

		if hasattr(self, 'onMessageReceived' + signalingType):
			getattr(self, 'onMessageReceived' + signalingType)(message)

		else:
			self.Logger.Warning(f'Signaling type {signalingType} appears to be unknown or no method onMessageReceived{signalingType} was associated with it.')

	def onMessageReceivedNewchat(self,  message: dict):
		content = message.get('content', None)
		if not content:
			self.Logger.Error('content was misssing from message.')
			return
		
		newChat = [
			content.get('localTime', str(datetime.now())),
			content.get('from', 'Unknown user.'),
			content.get('chatContent', 'Empty message.')
		]

		self.ChatDAT.appendRow(newChat)

		return

	def onMessageSendingNewchat(self, chatContent:str='') -> None:
			"""
			An event callback triggered when a local offer was made and a local SDP
			description was set.

			Args:
				connectionId (str): The ID of the RTCPeerConnection for which
				Signaling messages are being exchanged.
				localSdp (str): The SDP of this end of the RTCPeerConnection.
			"""
			content = {
				'localTime': str(datetime.now()),
				'from': self.SignalingClient.par.Clientname.eval(),
				'chatContent': chatContent
			}

			message = {
				'metadata': self.messagesMetadata,
				'signalingType': 'Newchat',
				'sender': self.SignalingClient.AsClient.address.val,
				'target': '',
				'content': content
			}

			self.ChatDAT.appendRow([
				content['localTime'],
				content['from'],
				content['chatContent'],
	 		])
			
			self.SignalingClient.Send(message)
			return

	"""
	UI
	"""
	def SendChat(self, newChat:str=''):
		if not newChat:
			self.Logger.Warning('No message was available, aborting.')
			return
		
		self.onMessageSendingNewchat(chatContent=newChat)
		return

	"""
	Par Callbacks
	"""
	def onSignalingclientChange(self, par) -> None:
		"""
		Called when the SignalingClient Par changed to trigger the Subscribe
		process again.

		Args:
			par (par): The SignalingClient Par.
		"""
		self.SignalingClient = par.eval()
		self.Subscribe()

	"""
	Utilities
	"""
	def Reset(self) -> None:
		"""
		Reset the Room session and all states of the Room COMP and its
		RoomExt.
		"""
		self.ChatDAT.clear(keepFirstRow=True)
		self.Subscribe()
		self.signalingCheckTimer.par.start.pulse()

	def isVersionMatching(self, apiVersion: str) -> bool:
		"""
		This method is used to confirm that the Signaling API version is
		matching between clients and server.

		Args:
			apiVersion (str): A version number as a string, to compare with the
			signalingServer COMP own version.

		Returns:
			bool: A boolean that represents whether the version is matching or
			not.
		"""
		if version.parse(apiVersion) != version.parse(self.ownerComp.par.Signalingapiversion.eval()):
			self.Logger.Error(f'API version of client {apiVersion} does not match API version of server {self.ownerComp.par.Signalingapiversion.eval()}. Aborting.')
			return False

		else:
			return True

	def Subscribe(self, signalingClient=None) -> bool:
		"""
		This method is called on init of the RoomExt or when the
		SignalingClient Par changed.

		It is using the Subscribe features of the SignalingClient COMP.

		Args:
			signalingClient (COMP, optional): An optional SignalingClient
			COMP. Attempt to use an already registered SignalingClient COMP
			when None was passed. Defaults to None.

		Returns:
			bool: Whether the subscription to the SignalingClient succeeded
			or not.
		"""

		signalingClient = self.SignalingClient if not signalingClient else signalingClient

		success = False
		if signalingClient and hasattr(signalingClient, 'Subscribe'):
			success = getattr(signalingClient, 'Subscribe')(
				self.ownerComp, self.SignalingClientMessagesTypes)

		return success

	def signalingCheck(self) -> bool:
		"""
		This method is called regularly to keep the link alive between the
		referenced SignalingClient and the Room COMP

		Returns:
				bool: Whether the link is still up and running.
		"""
		if self.SignalingClient and self.ownerComp in [subscriber['origin'] for subscriber in self.SignalingClient.Subscribers]:
			return True

		else:
			success = self.Subscribe()

			if not success:
				self.Logger.Error(
					f'Fatal error, the Room COMP could not subscribe to the signaling client or no signaling client was found. Aborting.')
				return success

			return success