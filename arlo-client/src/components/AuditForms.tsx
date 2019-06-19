import React from 'react'
import styled from 'styled-components';

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

const AuditForms = () => {

    const renderSelectMenu = () => {

        let obj = {
            array: [] as number[]
        };
    
        for (var i=0; i < 100; i++){
            obj.array[i] = i+1;
        };

    }

    const parseFile = () => {}

    
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
                        <Field/>
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
                                    <Field/>
                                    <FieldRight/>
                            </InputFieldRow>
                            <InputLabelRow>
                                <InputLabel>Name of Candidate/Choice 1</InputLabel>
                                <InputLabelRight>Votes for Candidate/Choice 1</InputLabelRight>
                            </InputLabelRow>
                            <InputFieldRow>     
                                <Field/>
                                <FieldRight/>
                            </InputFieldRow>
                        </TwoColumnSection>
                        </Section>
                        <Section>
                            <SectionLabel>Total Ballots Cast</SectionLabel>
                            <SectionDetail>Enter the overall number of ballot cards cast in jurisdictoins containing this contest.</SectionDetail>
                            <Field/>
                        </Section>
                        <SectionTitle>Audit Settings</SectionTitle>
                        <Section>
                            <SectionLabel>Desired Risk Limit</SectionLabel>
                            <SectionDetail>Set the risk for the audit as as percentage (e.g. "5" = 5%).</SectionDetail>
                            <select>
                                <option>1</option>
                                <option>2</option>
                                <option>3</option>
                                <option>4</option>
                                <option>5</option>
                            </select>
                        </Section>
                        <Section>
                            <SectionLabel>Random Seed</SectionLabel>
                            <SectionDetail>Enter the random number to seed the pseudo-random number generator.</SectionDetail>
                            <Field/>
                        </Section>
            </PageSection>
            <ButtonBar>
                <Button>Estimate Sample Size</Button>
            </ButtonBar>
            </form>

            {/* Form 2 */}

            <form>
                <PageSection>
                        <Section>
                            <SectionLabel>Estimated Sample Size</SectionLabel>
                            <SectionDetail>
                                Choose the initial sample size you would like to use for Round 1 of the audit from the options below.
                                    <div><input type="radio"/><InputLabel>223 samples (80% chance of reaching risk limit in one round)</InputLabel></div>
                                    <div><input type="radio"/><InputLabel>456 samples (90% chance of reaching risk limit in one round)</InputLabel></div>
                            </SectionDetail>
                        </Section>  
                        <Section>
                            <SectionLabel>Number of Audit Boards</SectionLabel>
                            <SectionDetail>Set the number of audit boards you wish to use.</SectionDetail>
                            <select>
                                <option>1</option>
                                <option>2</option>
                                <option>3</option>
                                <option>4</option>
                                <option>5</option>
                            </select>
                        </Section>
                        <Section>
                            <SectionLabel>Ballot Manifest</SectionLabel>    
                            <SectionDetail>Click "Browse" to choose the appropriate Ballot Manifest file from your computer</SectionDetail>
                            <input type="file" onClick={parseFile}></input>
                        </Section>
                </PageSection>         
                <ButtonBar>
                    <Button>Select Ballots To Audit</Button>
                </ButtonBar>
            </form>

            {/* Form 3 */}
            <form>
            <PageSection>
            <Section>
                <SectionLabel>Ballot Retrieval List</SectionLabel>
                <InlineButton>Download Ballot Retrieval List for Round 1</InlineButton>
                <SectionLabel>Audited Results: Round 1</SectionLabel>
                <SectionDetail>Enter the number of votes recorded for each candidate/choice in the audited ballots for Round 1</SectionDetail>
                <InputSection>
                    <InlineInput><InputLabel>Jane Doe III</InputLabel><Field/></InlineInput>
                    <InlineInput><InputLabel>Martin Van Buren</InputLabel><Field/></InlineInput>
                </InputSection>             
            </Section>
            </PageSection>
            <ButtonBar>
                <Button>Calculate Risk Measurement</Button>
            </ButtonBar>
            </form>

            {/* Form 4 */}
            <form>
                <Section>
                    <PageSection>
                        <SectionLabel>Audit Status: </SectionLabel>
                        <InputSection>
                            <InlineInput><InputLabel>Risk Limit: </InputLabel></InlineInput>
                            <InlineInput><InputLabel>Risk Measurement: </InputLabel></InlineInput>
                            <InlineInput><InputLabel>P-value: </InputLabel></InlineInput>
                        </InputSection> 
                        <SmallInlineButton>Download Audit Report</SmallInlineButton>
                    </PageSection>
                </Section>
            </form>

        </React.Fragment>
    );

}

export default AuditForms