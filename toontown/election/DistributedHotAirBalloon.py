from pandac.PandaModules import *
from otp.nametag.NametagConstants import *
from direct.distributed.ClockDelta import *
from direct.interval.IntervalGlobal import *
from direct.distributed.DistributedObject import DistributedObject
from direct.fsm.FSM import FSM
from toontown.toon import NPCToons
from toontown.toonbase import ToontownGlobals
from direct.task import Task
from random import choice
import ElectionGlobals

class DistributedHotAirBalloon(DistributedObject, FSM):
    def __init__(self, cr):
        DistributedObject.__init__(self, cr)
        FSM.__init__(self, 'HotAirBalloonFSM')
        self.avId = 0
        self.flightPathIndex = 0

        # Create the balloon
        self.balloon = loader.loadModel('phase_4/models/events/election_buddyBalloon-static')
        self.balloon.reparentTo(base.render)
        self.balloon.setPos(*ElectionGlobals.BalloonBasePosition)
        self.balloon.setScale(ElectionGlobals.BalloonScale)
        # So we can reparent toons to the balloon so they don't fall out
        self.cr.parentMgr.registerParent(ToontownGlobals.SPBuddysBalloon, self.balloon)
        # Balloon collision NodePath (outside)
        self.collisionNP = self.balloon.find('**/Collision_Outer')

        self.buddy = NPCToons.createLocalNPC(91915)
        self.buddy.setPos(0.7, 0.7, 0.4)
        self.buddy.setH(150)
        self.buddy.setScale((1/ElectionGlobals.BalloonScale)) # We want a normal sized Buddy
        self.buddy.loop('neutral')

        # Create balloon flight paths and Buddy speeches. It's important we do this AFTER we load everything
        # else as this requires both the balloon and Buddy.
        self.flightPaths = ElectionGlobals.generateFlightPaths(self)
        self.toonFlightPaths = ElectionGlobals.generateToonFlightPaths(self)
        self.speechSequence = ElectionGlobals.generateSpeechSequence(self)
        
    def delete(self):
        # Clean up after our mess...
        # This is what happens when you don't clean up:
        # http://puu.sh/77zAm.jpg
        self.demand('Off')
        self.ignore('enter' + self.collisionNP.node().getName())
        self.cr.parentMgr.unregisterParent(ToontownGlobals.SPBuddysBalloon)
        self.balloon.removeNode()
        if self.buddy:
            self.buddy.delete()
        DistributedObject.delete(self)
        
    def setState(self, state, timestamp, avId):
        if avId != self.avId:
            self.avId = avId
        self.demand(state, globalClockDelta.localElapsedTime(timestamp))
            
    def enterWaiting(self, offset):
        # Render Buddy, since we're going to be giving rides
        self.buddy.reparentTo(self.balloon)

        # Wait for a collision...
        self.accept('enter' + self.collisionNP.node().getName(), self.__handleToonEnter)
        # Mini animation for the balloon hovering near the floor
        self.balloonIdle = Sequence(
            Wait(0.3),
            self.balloon.posInterval(3, (-15, 33, 1.5)),
            Wait(0.3),
            self.balloon.posInterval(3, (-15, 33, 1.1)),
        )
        self.balloonIdle.loop()
        self.balloonIdle.setT(offset)
    
    def enterElectionIdle(self, offset):
        # Buddy is off for the election, but he left his balloon parked in TTC.
        self.balloon.setPos(*ElectionGlobals.BalloonElectionPosition)
        self.balloon.setH(283)
        self.balloonElectionIdle = Sequence(
            self.balloon.posInterval(3, (166.5, 64.0, 52.0), blendType='easeInOut'),
            self.balloon.posInterval(3, (166.5, 64.0, 53.0), blendType='easeInOut'),
        )
        self.balloonElectionIdle.loop()
        self.balloonElectionIdle.setT(offset)
        


    def __handleToonEnter(self, collEntry):
        if self.avId != 0:
            # Someone is already occupying the balloon
            return
        if self.state != 'Waiting':
            # The balloon isn't waiting for a toon
            return
        self.sendUpdate('requestEnter', [])
        
    def exitWaiting(self):
        self.balloonIdle.finish()
        self.ignore('enter' + self.collisionNP.node().getName())

    def exitElectionIdle(self):
        self.balloonElectionIdle.finish()

    def enterOccupied(self, offset):
        if self.avId == base.localAvatar.doId:
            # This is us! We need to reparent to the balloon and position ourselves accordingly.
            base.localAvatar.disableAvatarControls()
            
            self.hopOnAnim = Sequence(Parallel(
                Func(base.localAvatar.b_setParent, ToontownGlobals.SPBuddysBalloon), # Required to put the toon in the basket
                Func(base.localAvatar.b_setAnimState, 'jump', 1.0)), 
                base.localAvatar.posInterval(0.6, (0, 0, 2)), 
                base.localAvatar.posInterval(0.4, (0, 0, 0.7)), 
                Func(base.localAvatar.enableAvatarControls),
                Parallel(Func(base.localAvatar.b_setParent, ToontownGlobals.SPRender))) # Unparent the toon and balloon

            self.hopOnAnim.start()
        try:
            self.speechSequence = self.speechSequence
            self.speechSequence.start()
            self.speechSequence.setT(offset)
        except Exception, e:
            self.notify.debug('Exception: %s' % e)
        
    def exitOccupied(self):
        try:
            self.hopOnAnim.finish()
        except Exception, e:
            self.notify.debug('Exception: %s' % e)

    def setFlightPath(self, flightPathIndex):
        self.flightPathIndex = flightPathIndex
        
    def enterStartRide(self, offset):
        # Try and get the flightPath from the AI
        try:
            self.rideSequence = self.flightPaths[self.flightPathIndex]
            self.rideSequence.start()
            self.rideSequence.setT(offset)
        except Exception, e:
            self.notify.debug('Exception: %s' % e)

        if self.avId == base.localAvatar.doId:
            try:
                self.toonRideSequence = self.toonFlightPaths[self.flightPathIndex]
                self.toonRideSequence.start()
                self.toonRideSequence.setT(offset)
            except Exception, e:
                self.notify.debug('Exception: %s' % e)            
        
    def exitStartRide(self):
        try:
            self.rideSequence.finish()
            self.speechSequence.finish()
        except Exception, e:
            self.notify.debug('Exception: %s' % e) 

    def enterRideOver(self, offset):
        if self.avId == base.localAvatar.doId:
            # We were on the ride! Better reparent to the render and get out of the balloon...
            base.localAvatar.disableAvatarControls()

            self.hopOffAnim = Sequence(
                Parallel(Func(base.localAvatar.b_setParent, ToontownGlobals.SPRender), Func(base.localAvatar.b_setAnimState, 'jump', 1.0)), 
                Wait(0.3), 
                base.localAvatar.posInterval(0.3, (-14, 25, 6)), 
                base.localAvatar.posInterval(0.7, (-14, 20, 0)), 
                Wait(0.3), 
                Func(base.localAvatar.enableAvatarControls), 
                Wait(0.3), 
                Func(base.localAvatar.b_setAnimState, 'neutral')
                )

            self.hopOffAnim.start()
        