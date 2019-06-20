import React from 'react'
import styled from 'styled-components';
import uuid from 'uuid/v1';

const PageTitle = styled.div`
    font-size: .9em;
    font-weight: bold;
    margin: 0 0 25px 0;
`

const Section = styled.div`
    margin 50px 0 50px 0;
`

const SectionTitle = styled.div`
    font-size: .8em;
    text-align: center; 
    margin: 0 0 25px 0;
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
    display: inline-block;
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

function api<T>(endpoint: string, options: any): Promise<T> {
    console.log("options: ", options)
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
            // form 1
            name: "",
            randomSeed: 0,
            candidateOneName: "",
            candidateOneVotes: 0,
            candidateTwoName: "",
            candidateTwoVotes: 0,
            totalBallots: 0,
            desiredRiskLimit: 1,
            // form 2
            showFormTwo: false,
            showFormThree: false,
            showFormFour: false,
            sampleSize: "",
            auditBoards: 1,
        };
    }

    inputChange(e: any): any {
        console.log(e.target.name, ': ', e.target.value)
        this.setState({ [e.target.name]: e.target.value });
    }

    componentDidMount() {
        api("/audit/status", {})
            .then(res => {
                console.log("/audit/status: ", res)
            })
    }

    submitFormOne(e: any) {
        e.preventDefault();
        const {
            name, randomSeed, desiredRiskLimit,
            candidateOneName, candidateOneVotes,
            candidateTwoName, candidateTwoVotes,
            totalBallots
        } = this.state
        const data: Audit = {
            name,
            randomSeed: Number(randomSeed),
            riskLimit: Number(desiredRiskLimit),
            contests: [
                {
                    id: uuid(),
                    name,
                    totalBallotsCast: Number(totalBallots),
                    choices: [
                        {
                            id: uuid(),
                            name: candidateOneName,
                            numVotes: Number(candidateOneVotes)
                        },
                        {
                            id: uuid(),
                            name: candidateTwoName,
                            numVotes: Number(candidateTwoVotes)
                        }
                    ]
                },
            ]
        };
        api(`${apiBaseURL}/audit/basic`, {
            method: "POST",
            body: JSON.stringify(data),
            headers: {
                "Content-Type": "application/json"
            }
        }).then(res => {
            console.log("result: ", res);
            this.setState({ showFormTwo: true })
        }).catch(err => {
            console.log("error: ", err);
        })
    }

    fileInputChange(e: any) {
        console.log(e.target.files[0]);
    }

    submitFormTwo(e: any) {
        e.preventDefualt();
        // TODO: Api endpoints not yet clear
    }

    generateOptions(count: number): Array<JSX.Element> {
        let elements: Array<JSX.Element> = [];
        for (let i: number = 1; i <= count; i++) {
            elements.push(<option key={i.toString()}>{i}</option>)
        }
        return elements;
    }

    downloadBallotRetrievalList(e: any) {
        e.preventDefault();
        // ToDo what is jurisdiction id?
        const id: number = 1;
        api(`/jurisdiction/${id}/retrieval-list`, {})
            .then(res => {
                console.log("res: ", res);
            })
    }

    calculateRiskMeasurement(e: any) {
        e.preventDefualt();
        // ToDo: validate endpoint
    }

    downloadAuditReport(e: any) {
        e.preventDefault();
        // ToDo: validate endpoint
    }

    render() {
        return (
            <React.Fragment>
                <PageTitle>Audit Setup</PageTitle>

                {/* Form 1 */}

                <form>
                    <PageSection>
                        <SectionTitle>Contest Information</SectionTitle>
                        <Section>
                            <SectionLabel>Contest Name</SectionLabel>
                            <SectionDetail>Enter the name of the contest that will drive the audit.</SectionDetail>
                            <Field name="name" onChange={e => this.inputChange(e)} />
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
                                    <Field name="candidateOneName" onChange={e => this.inputChange(e)} />
                                    <FieldRight type="number" name="candidateOneVotes" onChange={e => this.inputChange(e)} />
                                </InputFieldRow>
                                <InputLabelRow>
                                    <InputLabel>Name of Candidate/Choice 1</InputLabel>
                                    <InputLabelRight>Votes for Candidate/Choice 1</InputLabelRight>
                                </InputLabelRow>
                                <InputFieldRow>
                                    <Field name="candidateTwoName" onChange={e => this.inputChange(e)} />
                                    <FieldRight type="number" name="candidateTwoVotes" onChange={e => this.inputChange(e)} />
                                </InputFieldRow>
                            </TwoColumnSection>
                        </Section>
                        <Section>
                            <SectionLabel>Total Ballots Cast</SectionLabel>
                            <SectionDetail>Enter the overall number of ballot cards cast in jurisdictoins containing this contest.</SectionDetail>
                            <Field type="number" name="totalBallots" onChange={e => this.inputChange(e)} />
                        </Section>
                        <SectionTitle>Audit Settings</SectionTitle>
                        <Section>
                            <SectionLabel>Desired Risk Limit</SectionLabel>
                            <SectionDetail>Set the risk for the audit as as percentage (e.g. "5" = 5%).</SectionDetail>
                            <select name="desiredRiskLimit" value={this.state.desiredRiskLimit} onChange={e => this.inputChange(e)}>
                                {
                                    this.generateOptions(100)
                                }
                            </select>
                        </Section>
                        <Section>
                            <SectionLabel>Random Seed</SectionLabel>
                            <SectionDetail>Enter the random number to seed the pseudo-random number generator.</SectionDetail>
                            <Field type="number" name="randomSeed" onChange={e => this.inputChange(e)} />
                        </Section>
                    </PageSection>
                    <ButtonBar>
                        <Button onClick={e => this.submitFormOne(e)}>Estimate Sample Size</Button>
                    </ButtonBar>
                </form>

                {/* Form 2 */}
                {this.state.showFormTwo &&
                <form>
                    <PageSection>
                        <Section>
                            <SectionLabel>Estimated Sample Size</SectionLabel>
                            <SectionDetail>
                                Choose the initial sample size you would like to use for Round 1 of the audit from the options below.
                                    <div><input name="sampleSize" type="radio" value="223" onChange={e => this.inputChange(e)} /><InputLabel>223 samples (80% chance of reaching risk limit in one round)</InputLabel></div>
                                <div><input name="sampleSize" type="radio" value="456" onChange={e => this.inputChange(e)} /><InputLabel>456 samples (90% chance of reaching risk limit in one round)</InputLabel></div>
                            </SectionDetail>
                        </Section>
                        <Section>
                            <SectionLabel>Number of Audit Boards</SectionLabel>
                            <SectionDetail>Set the number of audit boards you wish to use.</SectionDetail>
                            <select name="auditBoards" value={this.state.auditBoards} onChange={e => this.inputChange(e)}>
                                {this.generateOptions(5)}
                            </select>
                        </Section>
                        <Section>
                            <SectionLabel>Ballot Manifest</SectionLabel>
                            <SectionDetail>Click "Browse" to choose the appropriate Ballot Manifest file from your computer</SectionDetail>
                            <input type="file" accept=".csv" onChange={e => this.fileInputChange(e)}></input>
                        </Section>
                    </PageSection>
                    <ButtonBar>
                        <Button onClick={e => this.submitFormTwo(e)}>Select Ballots To Audit</Button>
                    </ButtonBar>
                </form>
                }
                {/* Form 3 */}
                {this.state.showFormThree &&
                <form>
                    <PageSection>
                        <Section>
                            <SectionLabel>Ballot Retrieval List</SectionLabel>
                            <InlineButton onClick={e => this.downloadBallotRetrievalList(e)}>Download Ballot Retrieval List for Round 1</InlineButton>
                            <SectionLabel>Audited Results: Round 1</SectionLabel>
                            <SectionDetail>Enter the number of votes recorded for each candidate/choice in the audited ballots for Round 1</SectionDetail>
                            <InputSection>
                                <InlineInput><InputLabel>Jane Doe III</InputLabel><Field /></InlineInput>
                                <InlineInput><InputLabel>Martin Van Buren</InputLabel><Field /></InlineInput>
                            </InputSection>
                        </Section>
                    </PageSection>
                    <ButtonBar>
                        <Button onClick={e => this.calculateRiskMeasurement(e)}>Calculate Risk Measurement</Button>
                    </ButtonBar>
                </form>
                }

                {/* Form 4 */}
                {this.state.showFormFour &&
                <form>
                    <Section>
                        <PageSection>
                            <SectionLabel>Audit Status: INCOMPLETE</SectionLabel>
                            <InputSection>
                                <InlineInput><InputLabel>Risk Limit: </InputLabel></InlineInput>
                                <InlineInput><InputLabel>Risk Measurement: </InputLabel></InlineInput>
                                <InlineInput><InputLabel>P-value: </InputLabel></InlineInput>
                            </InputSection>
                            <SectionLabel>Ballot Retrieval List</SectionLabel>
                            <InlineButton>Download Ballot Retrieval List for Round 2</InlineButton>
                            <SectionLabel>Audited Results: Round 2</SectionLabel>
                            <SectionDetail>Enter the number of votes recorded for each candidate/choice in the audited ballots for Round 2</SectionDetail>
                            <InputSection>
                                <InlineInput><InputLabel>Jane Doe III</InputLabel><Field /></InlineInput>
                                <InlineInput><InputLabel>Martin Van Buren</InputLabel><Field /></InlineInput>
                            </InputSection>
                            <SmallInlineButton onClick={e => this.downloadAuditReport(e)}>Download Audit Report</SmallInlineButton>
                        </PageSection>
                    </Section>
                </form>
                }

            </React.Fragment>
        );
    }

}

export default AuditForms;