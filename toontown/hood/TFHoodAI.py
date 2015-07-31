from toontown.hood import HoodAI
from toontown.toonbase import ToontownGlobals
from toontown.safezone.DistributedPicnicBasketAI import DistributedPicnicBasketAI
from toontown.hood import ZoneUtil
from toontown.safezone.DistributedPicnicTableAI import DistributedPicnicTableAI

class TFHoodAI(HoodAI.HoodAI):
    def __init__(self, air):
        HoodAI.HoodAI.__init__(self, air,
                               ToontownGlobals.Toonfest,
                               ToontownGlobals.Toonfest)
        self.timer = None
        self.picnicTables = []
        self.gameTables = []                      
	self.startup()
    
    def startup(self):
        HoodAI.HoodAI.startup(self)

        self.createTimer()
        #self.createPicnicTables()
        if simbase.config.GetBool('want-game-tables', True):
            self.createGameTables()

    def createTimer(self):
        self.timer = DistributedTimerAI(self.air)
        self.timer.generateWithRequired(self.zoneId)


    def findPicnicTables(self, dnaGroup, zoneId, area, overrideDNAZone=False):
        picnicTables = []
        if isinstance(dnaGroup, DNAGroup) and ('picnic_table' in dnaGroup.getName()):
            nameInfo = dnaGroup.getName().split('_')
            for i in xrange(dnaGroup.getNumChildren()):
                childDnaGroup = dnaGroup.at(i)
                if 'picnic_table' in childDnaGroup.getName():
                    pos = childDnaGroup.getPos()
                    hpr = childDnaGroup.getHpr()
                    picnicTable = DistributedPicnicBasketAI(
                        simbase.air, nameInfo[2],
                        pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                    picnicTable.generateWithRequired(zoneId)
                    picnicTables.append(picnicTable)
        elif isinstance(dnaGroup, DNAVisGroup) and (not overrideDNAZone):
            zoneId = ZoneUtil.getTrueZoneId(int(dnaGroup.getName().split(':')[0]), zoneId)
        for i in xrange(dnaGroup.getNumChildren()):
            foundPicnicTables = self.findPicnicTables(
                dnaGroup.at(i), zoneId, area, overrideDNAZone=overrideDNAZone)
            picnicTables.extend(foundPicnicTables)
        return picnicTables

    def createPicnicTables(self):
        self.picnicTables = []
        for zoneId in self.getZoneTable():
            dnaData = self.air.dnaDataMap.get(zoneId, None)
            zoneId = ZoneUtil.getTrueZoneId(zoneId, self.zoneId)
            if dnaData.getName() == 'root':
                area = ZoneUtil.getCanonicalZoneId(zoneId)
                foundPicnicTables = self.findPicnicTables(
                    dnaData, zoneId, area, overrideDNAZone=True)
                self.picnicTables.extend(foundPicnicTables)
        for picnicTable in self.picnicTables:
            picnicTable.start()

    def findGameTables(self, dnaGroup, zoneId, area, overrideDNAZone=False):
        gameTables = []
        if isinstance(dnaGroup, DNAGroup) and ('game_table' in dnaGroup.getName()):
            for i in xrange(dnaGroup.getNumChildren()):
                childDnaGroup = dnaGroup.at(i)
                if 'game_table' in childDnaGroup.getName():
                    pos = childDnaGroup.getPos()
                    hpr = childDnaGroup.getHpr()
                    gameTable = DistributedGameTableAI.DistributedGameTableAI(simbase.air)
                    gameTable.setPosHpr(pos[0], pos[1], pos[2], hpr[0], hpr[1], hpr[2])
                    gameTable.generateWithRequired(zoneId)
        elif isinstance(dnaGroup, DNAVisGroup) and (not overrideDNAZone):
            zoneId = ZoneUtil.getTrueZoneId(int(dnaGroup.getName().split(':')[0]), zoneId)
        for i in xrange(dnaGroup.getNumChildren()):
            foundGameTables = self.findGameTables(
                dnaGroup.at(i), zoneId, area, overrideDNAZone=overrideDNAZone)
            gameTables.extend(foundGameTables)
        return gameTables

    def createGameTables(self):
        self.gameTables = []
        for zoneId in self.getZoneTable():
            dnaData = self.air.dnaDataMap.get(zoneId, None)
            zoneId = ZoneUtil.getTrueZoneId(zoneId, self.zoneId)
            if dnaData.getName() == 'root':
                area = ZoneUtil.getCanonicalZoneId(zoneId)
                foundGameTables = self.findGameTables(
                    dnaData, zoneId, area, overrideDNAZone=True)
                self.gameTables.extend(foundGameTables)
    
