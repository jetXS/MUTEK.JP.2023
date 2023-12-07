# Day02.Signaling
The file shared in this Github repository is an ideal file for where we hope to get to within 2 hours of classes.

## Getting started
During this demo, I will heavily rely on an external editor, VS Code.

https://code.visualstudio.com/download

In TouchDesigner, you can use Ctrl+E to open a Text file into an external editor.

To link an external editor as the default editor to TouchDesigner, Go into Preferences -> DAT tab, and specify the External editor you wanna use.

If in the code you spot things referring to WebRTC, don't worry too much about it, it's likely because I grabbed some code from WebRTC related projects without updating some comments or variables.

## Signaling Server IP
The Signaling Client needs to connect to a Signaling Server. The Signaling Server file is shared in that repository. This is designed so that you can run the experiment outside of the workshop context if you wish. However, you will need to setup the network to meet your needs, including specifying Signaling Server IP and ports.

## Signaling, what is this ?
Base to WebRTC communications, but widely, it is a mean to connect 2 peers together through an intermediary.

## Signaling Client
On it's own, the signaling client is already working with the signaling server and can be used as a mean to "discover" clients on a network where clients don't know eachother, but they all know the server.

## Let's start hacking!

We are not really changing the Signaling Client COMP. We are adding a new COMP that will extend it.

### Create new COMP, add extension

```python
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
```

###  Add parameters
- SignalingClient parameter
- Signaling API Version
- Version

### Add Utilities code
- Add Timer CHOP
- Edit Timer callback
- Add Parameter Execute DAT
- Edit Parameter Execute DAT

### Add Generic Message received Method

```python
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
```

### Add Signaling Type received Method

```python
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
```

### Add Signaling Type received Method

```python
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
```

### Add the missing Signaling / Subscription methods

- Show how to find them and update them

### Hack / fix the Signaling Server to forward / passthrough properly

## Event CHOP, More instance, if time

## Credits

DynamicDoF is inspired by Lake Heckaman's DynamicDoF.
https://www.youtube.com/watch?v=3yC1xCHhIWA

### Assets
> industrial_sunset_puresky_4k.exr

https://polyhaven.com/a/industrial_sunset_puresky
Sergej Majboroda - CC0 License

> stylized_dirty_rock.sbsar

https://substance3d.adobe.com/assets/allassets/28f9b21fb5910b0a9d0963957eebf9e6b347eed8

> rust_brown.sbsar

https://substance3d.adobe.com/assets/allassets/3fcf23dbe96ef2799a78ccbb1fc98f1158724a50
