import React from 'react'
import Header from '../components/Header';
import AuditForms from '../components/AuditForms';


export interface RiskLimitingAudit {
    contestName: string
    candidateChoiceNames: any
    voteTotalsForEachCandidate: any
    totalBallotsCast: string
    riskLimit: any
    randomSeed: any
    estimatedSampleSize: any
    totalNumberOfAuditBoards: any
    ballotManifest: any
    ballotFileName: string
    ballotBatchesInFile: any
    ballotsInFile: any
    ballotRetrievalList: any
    candidateResults: any
    auditStatus: any
    riskMeasurement: any
    pValue: any
}

const AuditSetupPage = () => {
   
    return (
        <React.Fragment>
            <Header/>
            <AuditForms/>
        </React.Fragment>
    );
}

export default AuditSetupPage