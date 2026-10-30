import FWCore.ParameterSet.Config as cms
from Configuration.StandardSequences.Eras import eras

process = cms.Process("IN", eras.Phase2C17I13M9)
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.Geometry.GeometryExtendedRun4D110Reco_cff')
process.load('Configuration.Geometry.GeometryExtendedRun4D110_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, '150X_mcRun4_realistic_v1', '')

process.load('SimCalorimetry.HcalTrigPrimProducers.hcaltpdigi_cff')
process.load('CalibCalorimetry.CaloTPG.CaloTPGTranscoder_cfi')
process.load('Configuration.StandardSequences.SimL1Emulator_cff')
process.load('L1Trigger.TrackTrigger.TrackTrigger_cff')
process.load("L1Trigger.TrackFindingTracklet.L1HybridEmulationTracks_cff")
process.load("L1Trigger.TrackTrigger.Setup_cff")
process.load("L1Trigger.TrackerDTC.DTC_cff") # DTC_cff
process.load("RecoVertex.BeamSpotProducer.BeamSpot_cfi")
process.load('L1Trigger.L1THGCal.hgcalTriggerPrimitives_cff')

# Use VarParsing to handle input and output files for HTCondor jobs
from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing()
options.register('inputFile', '', VarParsing.multiplicity.singleton, VarParsing.varType.string, 'Input ROOT file')
options.register('outputFile', 'inputs170X.root', VarParsing.multiplicity.singleton, VarParsing.varType.string, 'Output ROOT file')
options.register('maxEvents', -1, VarParsing.multiplicity.singleton, VarParsing.varType.int, 'Maximum number of events to process')
options.parseArguments()

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(options.inputFile),
    inputCommands = cms.untracked.vstring(
        'keep *',
        # 'drop l1tPFJets_*_*_*',
        # 'drop l1tPFTaus_*_*_*',
        # 'drop l1tTrackerMuons_*_*_*',
        # 'drop *_hlt*_*_HLT', # needed for offline information, so keep
        'drop triggerTriggerFilterObjectWithRefs_*_*_HLT',
        'drop *_l1tLayer*_*_HLT',
    ),
)
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(options.maxEvents))
process.options = cms.untracked.PSet(
        wantSummary = cms.untracked.bool(True),
        numberOfThreads = cms.untracked.uint32(4),
        #numberOfStreams = cms.untracked.uint32(4),
)

process.PFInputsTask = cms.Task(
    process.L1TLayer1TaskInputsTask,
    process.L1THGCalTriggerPrimitivesTask,
    process.TTClustersFromPhase2TrackerDigis,
    process.TTStubsFromPhase2TrackerDigis,
    process.ProducerDTC,
    #process.offlineBeamSpot,
    process.l1tTTTracksFromTrackletEmulation,
    process.l1tTTTracksFromExtendedTrackletEmulation,
    process.TTTrackAssociatorFromPixelDigis,
    process.TTTrackAssociatorFromPixelDigisExtended,
    process.SimL1EmulatorTask,
#    process.l1tTkStubsGmt,
)
process.p = cms.Path(
        process.l1tLayer1 +
        process.l1tLayer2Deregionizer +
        process.l1tLayer2EG
)
process.p.associate(process.PFInputsTask)
process.p.associate(process.SimL1EmulatorTask)

process.out = cms.OutputModule(
        "PoolOutputModule",
        fileName = cms.untracked.string(options.outputFile),
        outputCommands = cms.untracked.vstring(
            "drop *",
            # --- GEN
            "keep *_genParticles_*_*",
            "keep *_genFilterEfficiencyProducer_*_*",
            "keep *_generator_*_*",
            "keep *_externalLHEProducer_*_*",
            "keep *_ak4GenJetsNoNu_*_*",
            "keep *_genMetTrue_*_*",
            # --- Track TPs
            "keep *_l1tTTTracksFromTrackletEmulation_*_*",
            "keep *_l1tTTTracksFromExtendedTrackletEmulation_*_*",
            "keep *_TTTrackAssociatorFromPixelDigis_*_*",
            "keep *_TTTrackAssociatorFromPixelDigisExtended_*_*",
            # --- Calo TPs
            "keep *_simEcalEBTriggerPrimitiveDigis_*_*",
            "keep *_simHcalTriggerPrimitiveDigis_*_*",
            "keep *_simCaloStage2Layer1Digis_*_*",
            "keep *_simCaloStage2Digis_*_*",
            # --- Muon TPs
            "keep *_simMuonRPCDigis_*_*",
            "keep *_simMuonGEMPadDigis_*_*",
            "keep *_simMuonGEMPadDigiClusters_*_*",
            "keep *_simDtTriggerPrimitiveDigis_*_*",
            "keep *_simCscTriggerPrimitiveDigis_*_*",
            "keep *_simTwinMuxDigis_*_*",
            "keep *_simBmtfDigis_*_*",
            "keep *_simKBmtfStubs_*_*",
            "keep *_simKBmtfDigis_*_*",
            "keep *_simEmtfDigis_*_*",
            "keep *_simOmtfDigis_*_*",
            "keep *_simGmtCaloSumDigis_*_*",
            "keep *_simGmtStage2Digis_*_*",
            "keep *_simEmtfShowers_*_*",
            "keep *_simGmtShowerDigis_*_*",
            "keep *_simCscTriggerPrimitiveDigisRun3_*_*",
            "keep *_simMuonME0PadDigis_*_*",
            "keep *_me0TriggerDigis_*_*",
            "keep *_simMuonME0PseudoReDigisCoarse_*_*",
            "keep *_me0RecHitsCoarse_*_*",
            "keep *_me0TriggerPseudoDigis_*_*",
            "keep *_me0RecHits_*_*",
            "keep *_me0Segments_*_*",
            "keep *_me0TriggerConvertedPseudoDigis_*_*",
            "keep *_simCscTriggerPrimitiveDigisPhase2_*_*",
            "keep *_simGtExtFakeStage2Digis_*_*",
            "keep *_simGtStage2Digis_*_*",
            "keep *_CalibratedDigis_*_*",
            "keep *_dtTriggerPhase2PrimitiveDigis_*_*",
            # --- HGCal TPs
            "keep l1tHGCalTriggerCellBXVector_l1tHGCalVFEProducer_*_*",
            #"keep l1tHGCalTriggerCellBXVector_l1tHGCalConcentratorProducer_*_*",
            "keep l1tHGCalMulticlusterBXVector_l1tHGCalBackEndLayer2Producer_*_*",
            "keep l1tHGCalTowerBXVector_l1tHGCalTowerProducer_*_*",
            # --- GCT reconstruction
            "keep *_l1tEGammaClusterEmuProducer_*_*",
            "keep *_l1tTowerCalibration_*_*",
            "keep *_l1tCaloJet_*_*",
            "keep *_l1tCaloJetHTT_*_*",
            # "keep *_l1tPhase2L1CaloEGammaEmulator_*_*",
            # "keep *_l1tPhase2CaloPFClusterEmulator_*_*",
            # --- GTT reconstruction
            "keep *_l1tVertexFinder_*_*",
            "keep *_l1tVertexFinderEmulator_*_*",
            "keep *_l1tTrackJets_*_*",
            "keep *_l1tTrackJetsExtended_*_*",
            "keep *_l1tTrackFastJets_*_*",
            "keep *_l1tTrackerEtMiss_*_*",
            "keep *_l1tTrackerHTMiss_*_*",
            "keep *_l1tTrackJetsEmulation_*_*",
            "keep *_l1tTrackJetsExtendedEmulation_*_*",
            "keep *_l1tTrackerEmuEtMiss_*_*",
            "keep *_l1tTrackerEmuHTMiss_*_*",
            "keep *_l1tTrackerEmuHTMissExtended_*_*",
            # --- GMT reconstruction
            "keep *_l1tStubsGmt_*_*",
            "keep *_l1tKMTFMuonsGmt_*_*",
            "keep *_l1tFwdMuonsGmt_*_*",
            "keep *_l1tSAMuonsGmt_*_*",
            # --- offline RECO information
            "keep *_slimmedJetsPuppi_*_*",
            "keep *_offlineSlimmedPrimaryVertices_*_*",
            "keep *_packedPFCandidates_*_*",
            "keep *_slimmedSecondaryVertices_*_*",
            "keep *_lostTracks_*_*",
            "keep *_slimmedGenJets_*_*",
            "keep *_slimmedElectrons_*_*",
            "keep *_slimmedMuons_*_*",
            "keep *_slimmedPhotons_*_*",
            "keep *_slimmedTaus_*_*",
            "keep *_reducedEgamma_*_*",
        ),
        compressionAlgorithm = cms.untracked.string('LZMA'),
        compressionLevel = cms.untracked.int32(4),
        dropMetaData = cms.untracked.string('ALL'),
        fastCloning = cms.untracked.bool(False),
        overrideInputFileSplitLevels = cms.untracked.bool(True),
        eventAutoFlushCompressedSize = cms.untracked.int32(15728640),
        SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring("p")),
)
process.e = cms.EndPath(process.out)
process.schedule = cms.Schedule([process.p,process.e])
process.out.outputCommands += [ "drop *_l1tHGCalVFEProducer_*_*", ]
