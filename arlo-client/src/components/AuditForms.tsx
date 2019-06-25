import React from 'react'
import styled from 'styled-components';

const Section = styled.div`
    margin 20px 0 20px 0;
`

const SectionTitle = styled.div`
    font-size: .8em;
    text-align: center; 
    margin: 40px 0 25px 0;
`
const SectionDetail = styled.div`
    font-size: .4em;
    margin-top: 10px;
`

const SectionLabel = styled.div`
    font-size: .5em;
    font-weight: bold;
`
const PageSection = styled.div`
    text-align: left;
    display: block;
    width: 50%;
`

const InputSection = styled.div`
    width: 100%;
    display: block;
    margin-top: 25px;
    font-size: .4em;
`

const TwoColumnSection = styled.div`
    width: 100%;
    display: block;
    margin-top: 25px;
    font-size: .4em;
`

const InputLabelRow = styled.div`
    width: 100%;
    display: flex; 
    flex-direction: row;
    margin-bottom: 10px;
`
const InputFieldRow = styled.div`
    width: 100%;
    display: flex; 
    flex-direction: row;
    margin-bottom: 25px;
`

const Field = styled.input`
    width: 45%;
`

const FieldRight = styled.input`
    width: 45%;
    margin-left: 50px;
`

const InputLabel = styled.label`
    display: inline-block;
`

const InputLabelRight = styled.label`
    margin-left: 75px;
`

const InlineInput = styled.div`
    width: 50%;
    display: flex; 
    flex-direction: row;
    justify-content: space-between;
    margin-bottom: 10px;
`

const ButtonBar = styled.div`
    margin 50px 0 50px 0;
    text-align: center;
`

const Button = styled.button`
    background: rgb(211,211,211);
    font-weight: bold;
    font-size: .4em;
    color: black;
    width: 200px;
    height: 30px; 
    border-radius: 5px;
    margin: 0 auto;
`

const InlineButton = styled.button`
    background: rgb(211,211,211);
    font-weight: bold;
    font-size: .4em;
    color: black;
    width: 275px;
    height: 20px; 
    border-radius: 5px;
    margin 10px 0 30px 0;
`

const SmallInlineButton = styled.button`
    background: rgb(211,211,211);
    font-weight: bold;
    font-size: .4em;
    color: black;
    width: 170px;
    height: 20px; 
    border-radius: 5px;
    margin 10px 0 30px 0;
`
const apiBaseURL = "";
interface Candidate {
    id: string,
    name: string,
    numVotes: number
};

interface Contest {
    id: string,
    name: string,
    choices: Array<Candidate>,
    totalBallotsCast: number
};

interface Audit {
    name: string,
    riskLimit: number,
    randomSeed: number,
    contests: Array<Contest>
};

interface AuditBoard {
    id: string,
    members: Array<any>
}

interface State {
    name: string,
    randomSeed: number,
    candidateOneName: string,
    candidateOneVotes: number,
    candidateTwoName: string,
    candidateTwoVotes: number,
    totalBallots: number,
    auditBoards: number,
    desiredRiskLimit: number
};

interface Jurisdiction {
    id: string,
    name: string,
    contests: Array<string>
    auditBoards: Array<AuditBoard>
}

function api<T>(endpoint: string, options: any): Promise<T> {
    return fetch(endpoint, options)
        .then(res => {
            if (!res.ok) {
                throw new Error(res.statusText)
            }
            return res.json() as Promise<T>
        })
}

class AuditForms extends React.Component<any, any>{
    // state: State;
    constructor(props: any) {
        super(props);
        this.state = {
            audit: null,
            // form 2
            showFormTwo: false,
            showFormThree: true,
            showFormFour: true,
            sampleSize: "",
            auditBoards: [],
            manifestCSV: null,
            manifestUploaded: false,
            // jurisdiction
            jurisdictionID: "",
            roundsExist: false,
            rounds: [],
            isLoading: false
        };
        this.generateFormThree = this.generateFormThree.bind(this);
    }

    inputChange(e: any): any {
        this.setState({ [e.target.name]: e.target.value });
    }

    async getStatus() {
        const audit: any = await api("/audit/status", {})
        console.log("res: ", audit)
        return audit
    }

  async componentDidMount() {
    const audit = await this.getStatus()
    this.setState({audit})
  }

  async submitFormOne(e: any) {
        e.preventDefault();
    this.setState({ canEstimateSampleSize: false })
    const formData = new FormData(document.getElementById('formOne') as HTMLFormElement)
        const data: Audit = {
            name: 'Election',
            randomSeed: Number(formData.get('randomSeed')),
            riskLimit: Number(formData.get('desiredRiskLimit')),
            contests: [
                {
                    id: 'contest-1',
                    name: formData.get('name') as string,
                    totalBallotsCast: Number(formData.get('totalBallotsCast')),
                    choices: [
                        {
                            id: 'candidate-1',
                            name: formData.get('candidateOneName') as string,
                            numVotes: Number(formData.get('candidateOneVotes'))
                        },
                        {
                            id: 'candidate-2',
                            name: formData.get('candidateTwoName') as string,
                            numVotes: Number(formData.get('candidateTwoVotes'))
                        }
                    ]
                },
            ]
        };
        try {
            this.setState({isLoading: true})
            await api(`${apiBaseURL}/audit/basic`, {
                method: "POST",
                body: JSON.stringify(data),
                headers: {
                    "Content-Type": "application/json"
                }
            });

            const audit: any = await api("/audit/status", {})
            console.log("res: ", audit)
            this.setState({ isLoading: false, audit });

        } catch (err) {
            console.log("error: ", err);
            this.setState({ canEstimateSampleSize: true });
        } finally {
            this.setState({isLoading: false})
        }
    }

    async fileInputChange(e: any) {
        const files: Array<any> = e.target.files;
        if (files.length < 1) {
            return; // no file selected
        }
        this.setState({ manifestCSV: files[0] })
    }

  async submitFormTwo(e: any) {
    e.preventDefault();
        const { manifestCSV } = this.state;

        const numAuditBoards = parseInt((document.getElementById('auditBoards') as HTMLInputElement).value);
    
        const auditBoards = Array.from(Array(numAuditBoards).keys()).map(i => {
            return {
                id: `audit-board-${i+1}`, members: []
            }
        })

        try {
            // upload jurisdictions
            const data: Array<Jurisdiction> = [{
                id: 'jurisdiction-1',
                name: 'Jurisdiction 1',
                contests: [`contest-1`],
                auditBoards: auditBoards,
            }];
            this.setState({isLoading: true})
            let res: any = await api("/audit/jurisdictions", {
                method: "POST",
                body: JSON.stringify({ jurisdictions: data }),
                headers: {
                    "Content-Type": "application/json"
                }
            })

            // get latest audit with jurisdiction id and use it to upload the data
            let audit: any = await api("/audit/status", {})
            this.setState({ audit })
            if (audit.jurisdictions.length < 1) {
                return;
            }
            const jurisdictionID: string = audit.jurisdictions[0].id

          // upload form data
            if (manifestCSV == null) {
                this.setState({ audit })
                return;
            }
            console.log("manifestCSV: ", manifestCSV)
            const formData: FormData = new FormData();
            formData.append("manifest", manifestCSV, manifestCSV.name);
            res = await api(`/jurisdiction/${jurisdictionID}/manifest`, {
                method: "POST",
                body: formData
            })
            console.log("Upload manifest response: ", res)

            audit = await api("/audit/status", {})
            this.setState({ audit, isLoading: false})
        } catch (err) {
            console.log("Error when Uploading manifest: ", err)
        }
        // TODO: Api endpoints not yet clear
    }

    generateOptions(count: number): Array<JSX.Element> {
        let elements: Array<JSX.Element> = [];
        for (let i: number = 1; i <= count; i++) {
            elements.push(<option key={i.toString()}>{i}</option>)
        }
        return elements;
    }

    getJurisdictionId() {
        return this.state.audit.jurisdictions[0].id
    }

    downloadBallotRetrievalList(id: number, e: any) {
        e.preventDefault();
        const jurisdictionID: string = this.getJurisdictionId()
        window.open(`/jurisdiction/${jurisdictionID}/${id}/retrieval-list`)
    }

    async deleteBallotManifest(e: any) {
        e.preventDefault();
        try {
            const jurisdictionID: string = this.state.audit.jurisdictions[0].id;
            await api(`/jurisdiction/${jurisdictionID}/manifest`, { method: "DELETE" });
            const audit: any = await api("audit/status", { method: "GET" })
            this.setState({ audit, manifestUploaded: false })
        } catch (err) {
            console.log("failed to delete ballot Manifest: ", err);
        }
    }

    async calculateRiskMeasurement(data: any, evt: any) {
        evt.preventDefault();
        const { id, round, candidateOne, candidateTwo } = data;
        console.log("calculateRiskMeasurement For Round: ", id, ", ", round)
        try {
            const jurisdictionID: string = this.state.audit.jurisdictions[0].id;
            console.log(jurisdictionID, 'jurisdictionID')
            const body: any = {
                "contests": [
                    {
                        id: "contest-1",
                        results: {
                            "candidate-1": Number(candidateOne),
                            "candidate-2": Number(candidateTwo)
                        }
                    }
                ]
            }

	  this.setState({isLoading:true})
            await  api(`/jurisdiction/${jurisdictionID}/${id}/results`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            })
            const audit: any = await this.getStatus();
            this.setState({ audit , isLoading:false})
        } catch (err) {
            console.log("failed to calcualteRiskManagement(): ", err);
        }
    }

    async downloadAuditReport(i: number, round: any, evt: any) {
        evt.preventDefault();
        try {
            console.log("Download Audit Report Form For Round: ", i, ", ", round)
            window.open(`/audit/report`)
            const audit: any = await this.getStatus();
            this.setState({ audit })
            console.log("status: ", audit)
        } catch (err) {
            console.log("downloadAuditReport: ", err)
        }
    }

    generateFormThree() {
        const { audit } = this.state;
        if (!audit) {
            return;
        }
        return audit.rounds.map((v: any, i: number) => {
            console.log("v.contests > 0: ", v.contests);
            const round: number = i + 1;
            const contest: any = v.contests.length > 0 ? v.contests[0] : null;
            console.log("contests: ", v.contests, ", v.contest[0]:", contest)
            let candidateOne: string = "";
          let candidateTwo: string = "";	
	  const showCalculateButton = (i+1) === audit.rounds.length && !contest.endMeasurements.isComplete
            return (
                <React.Fragment key={i}>
                      <PageSection>
                        <SectionTitle>Round {i+1}</SectionTitle>
			
                          <Section>
                              <SectionLabel>Ballot Retrieval List {contest ? `${contest.sampleSize} Ballots` : ""}</SectionLabel>
                              <InlineButton onClick={e => this.downloadBallotRetrievalList(round, e)}>Download Ballot Retrieval List for Round {i + 1}</InlineButton>
                              <SectionLabel>Audited Results: Round {round}</SectionLabel>
                              <SectionDetail>Enter the number of votes recorded for each candidate/choice in the audited ballots for Round {i + 1}</SectionDetail>
			      <form>
                              <InputSection>
                                <InlineInput onChange={(e: any) => candidateOne = e.target.value}><InputLabel>{this.state.audit.contests[0].choices[0].name}</InputLabel><Field /></InlineInput>
                                <InlineInput onChange={(e: any) => candidateTwo = e.target.value}><InputLabel>{this.state.audit.contests[0].choices[1].name}</InputLabel><Field /></InlineInput>
                              </InputSection>
			      </form>
                          </Section>
	      {this.state.isLoading &&
	       <p>Loading...</p>
	      }
		      {showCalculateButton &&
                       <ButtonBar>
                         <Button type="button" onClick={e => this.calculateRiskMeasurement({ id: round, round: v, candidateOne, candidateTwo, roundIndex: i }, e)}>Calculate Risk Measurement</Button>
                       </ButtonBar>
		      }
			  {contest && contest.endMeasurements.pvalue && (contest.endMeasurements.isComplete !== null) &&
                           <Section>
                             <SectionLabel>Audit Status: {contest.endMeasurements.isComplete ? "COMPLETE" : "INCOMPLETE"}</SectionLabel>
                             <InputSection>
                               <InlineInput ><InputLabel>Risk Limit: </InputLabel>{this.state.audit.riskLimit}%</InlineInput>
                               <InlineInput><InputLabel>P-value: </InputLabel> {contest.endMeasurements.pvalue}</InlineInput>
                             </InputSection>
                             {/* {Form 3} */}
                             {contest.endMeasurements.isComplete &&
                              <SmallInlineButton onClick={e => this.downloadAuditReport(i, v, e)}>Download Audit Report</SmallInlineButton>}
                           </Section>
			  }
                      </PageSection>
                </React.Fragment>
            )
        })
    }

  
    render() {
      const { audit } = this.state
      const formOneHasData = audit && audit.contests[0]
      const formTwoHasData = audit && audit.jurisdictions[0]
      const manifestUploaded = formTwoHasData && audit.jurisdictions[0].ballotManifest.filename
      const formThreeHasData = manifestUploaded && (audit.rounds.length>0)
        return (
            <React.Fragment>
                {/* Form 1 */}

                <form id="formOne">
                    <PageSection>
                        <SectionTitle>Contest Information</SectionTitle>
                        <Section>
                            <SectionLabel>Contest Name</SectionLabel>
                            <SectionDetail>Enter the name of the contest that will drive the audit.</SectionDetail>
                            <Field name="name" defaultValue={formOneHasData && this.state.audit.contests[0].name} />
                        </Section>
                        <Section>
                            <SectionLabel>Candidates/Choices & Vote Totals</SectionLabel>
                            <SectionDetail>Enter the name of each candidate choice that appears on the ballot for this contest.</SectionDetail>
                            <TwoColumnSection>
                                <InputLabelRow>
                                    <InputLabel>Name of Candidate/Choice 1</InputLabel>
                                    <InputLabelRight>Votes for Candidate/Choice 1</InputLabelRight>
                                </InputLabelRow>
                                <InputFieldRow>
                                    <Field name="candidateOneName" defaultValue={formOneHasData && this.state.audit.contests[0].choices[0].name} />
                                    <FieldRight type="number" name="candidateOneVotes" defaultValue={formOneHasData && this.state.audit.contests[0].choices[0].numVotes} />
                                </InputFieldRow>
                                <InputLabelRow>
                                    <InputLabel>Name of Candidate/Choice 2</InputLabel>
                                    <InputLabelRight>Votes for Candidate/Choice 2</InputLabelRight>
                                </InputLabelRow>
                                <InputFieldRow>
                                    <Field name="candidateTwoName" defaultValue={formOneHasData && this.state.audit.contests[0].choices[1].name} />
                                    <FieldRight type="number" name="candidateTwoVotes" defaultValue={formOneHasData && this.state.audit.contests[0].choices[1].numVotes} />
                                </InputFieldRow>
                            </TwoColumnSection>
                        </Section>
                        <Section>
                            <SectionLabel>Total Ballots Cast</SectionLabel>
                            <SectionDetail>Enter the overall number of ballot cards cast in jurisdictoins containing this contest.</SectionDetail>
                            <Field type="number" name="totalBallotsCast" defaultValue={formOneHasData && this.state.audit.contests[0].totalBallotsCast} />
                        </Section>
                        <SectionTitle>Audit Settings</SectionTitle>
                        <Section>
                            <SectionLabel>Desired Risk Limit</SectionLabel>
                            <SectionDetail>Set the risk for the audit as as percentage (e.g. "5" = 5%).</SectionDetail>
                            <select name="desiredRiskLimit" defaultValue={formOneHasData && this.state.audit.riskLimit}>
                                {
                                    this.generateOptions(20)
                                }
                            </select>
                        </Section>
                        <Section>
                            <SectionLabel>Random Seed</SectionLabel>
                            <SectionDetail>Enter the random number to seed the pseudo-random number generator.</SectionDetail>
                            <Field type="number" defaultValue={formOneHasData && this.state.audit.randomSeed} name="randomSeed" />
                        </Section>
                    </PageSection>
		    {!formOneHasData && this.state.isLoading &&
		     <p>Loading...</p>}
		    {!formOneHasData && !this.state.isLoading &&
                     <ButtonBar>
                       <Button onClick={e => this.submitFormOne(e)}>Estimate Sample Size</Button>
                     </ButtonBar>
		    }
                </form>

                {/* Form 2 */}
                {formOneHasData &&
                    <form onSubmit={e => this.submitFormTwo(e)} id="formTwo">
                        <PageSection>
                            {/* <Section>
                                <SectionLabel>Estimated Sample Size</SectionLabel>
                                <SectionDetail>
                                    Choose the initial sample size you would like to use for Round 1 of the audit from the options below.
                                    <div><input name="sampleSize" type="radio" value="223" onChange={e => this.inputChange(e)} /><InputLabel>223 samples (80% chance of reaching risk limit in one round)</InputLabel></div>
                                    <div><input name="sampleSize" type="radio" value="456" onChange={e => this.inputChange(e)} /><InputLabel>456 samples (90% chance of reaching risk limit in one round)</InputLabel></div>
                                </SectionDetail>
                            </Section> */}
                            <Section>
                                <SectionLabel>Number of Audit Boards</SectionLabel>
                                <SectionDetail>Set the number of audit boards you wish to use.</SectionDetail>
                                <select id="auditBoards" name="auditBoards" defaultValue={formTwoHasData && this.state.audit.jurisdictions[0].auditBoards.length}>
                                    {this.generateOptions(5)}
                                </select>
                            </Section>
                            <Section>
                                <SectionLabel>Ballot Manifest</SectionLabel>
                                {manifestUploaded ?
                                    <React.Fragment>
                                        <SectionDetail><b>Filename:</b> {audit.jurisdictions[0].ballotManifest.filename}</SectionDetail>
                                        <SectionDetail><b>Ballots:</b> {audit.jurisdictions[0].ballotManifest.numBallots}</SectionDetail>
                                        <SectionDetail><b>Batches:</b> {audit.jurisdictions[0].ballotManifest.numBatches}</SectionDetail>
					{!formThreeHasData &&
                                        <Button onClick={e => this.deleteBallotManifest(e)}>Delete File</Button>}
                                    </React.Fragment> :
                                    <React.Fragment>
                                        <SectionDetail>Click "Browse" to choose the appropriate Ballot Manifest file from your computer</SectionDetail>
                                        <input type="file" accept=".csv" onChange={e => this.fileInputChange(e)}></input>
                                    </React.Fragment>
                                }
                            </Section>
                        </PageSection>
			{!formThreeHasData && this.state.isLoading &&
			<p>Loading...</p>
			}
			{!formThreeHasData && !this.state.isLoading &&
                        <ButtonBar>
                            <Button onClick={e => this.submitFormTwo(e)}>Select Ballots To Audit</Button>
                        </ButtonBar>
			}
                    </form>
                }
                {/* Form 3 */}
                {this.generateFormThree()}

            </React.Fragment>
        );
    }
}

export default AuditForms;
