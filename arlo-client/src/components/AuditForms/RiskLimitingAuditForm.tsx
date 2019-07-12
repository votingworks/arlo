import React from 'react'
import { toast } from 'react-toastify'
import EstimateSampleSize from './EstimateSampleSize'
import SelectBallotsToAudit from './SelectBallotsToAudit'
import CalculateRiskMeasurement from './CalculateRiskMeasurement'

const apiBaseURL = ''
interface Candidate {
  id: string
  name: string
  numVotes: number
}

interface Contest {
  id: string
  name: string
  choices: Candidate[]
  totalBallotsCast: number
}

interface Audit {
  name: string
  riskLimit: number
  randomSeed: number
  contests: Contest[]
}

interface AuditBoard {
  id: string
  members: any[]
}

interface Jurisdiction {
  id: string
  name: string
  contests: string[]
  auditBoards: AuditBoard[]
}

function api<T>(endpoint: string, options: any): Promise<T> {
  return fetch(endpoint, options).then(res => {
    if (!res.ok) {
      throw new Error(res.statusText)
    }
    return res.json() as Promise<T>
  })
}

class AuditForms extends React.Component<any, any> {
  // state: State;
  public constructor(props: any) {
    super(props)
    this.state = {
      audit: '',
      canEstimateSampleSize: true,
      // form 2
      //showFormTwo: false,
      //showFormThree: true,
      //showFormFour: true,
      //sampleSize: '',
      //auditBoards: [],
      manifestCSV: '',
      //manifestUploaded: false,
      // jurisdiction
      //jurisdictionID: '',
      //roundsExist: false,
      //rounds: [],
      isLoading: false,
    }
  }

  public async componentDidMount() {
    const audit = await this.getStatus()
    this.setState({ audit })
  }

  public async getStatus() {
    const audit: any = await api('/audit/status', {})
    return audit
  }

  public getJurisdictionId() {
    return this.state.audit.jurisdictions[0].id
  }

  public submitFormOne = async (e: any) => {
    e.preventDefault()
    this.setState({ canEstimateSampleSize: false })
    const formData = new FormData(document.getElementById(
      'formOne'
    ) as HTMLFormElement)
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
              numVotes: Number(formData.get('candidateOneVotes')),
            },
            {
              id: 'candidate-2',
              name: formData.get('candidateTwoName') as string,
              numVotes: Number(formData.get('candidateTwoVotes')),
            },
          ],
        },
      ],
    }
    try {
      this.setState({ isLoading: true })
      await api(`${apiBaseURL}/audit/basic`, {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const audit: any = await api('/audit/status', {})
      this.setState({ isLoading: false, audit })
    } catch (err) {
      toast.error(err.message)
      this.setState({ canEstimateSampleSize: true })
    } finally {
      this.setState({ isLoading: false })
    }
  }

  public fileInputChange = async (e: any) => {
    const files: any[] = e.target.files
    if (files.length < 1) {
      return // no file selected
    }
    this.setState({ manifestCSV: files[0] })
  }

  public submitFormTwo = async (e: any) => {
    e.preventDefault()
    const { manifestCSV } = this.state

    const numAuditBoards = parseInt(
      (document.getElementById('auditBoards') as HTMLInputElement).value
    )

    const auditBoards = Array.from(Array(numAuditBoards).keys()).map(i => {
      return {
        id: `audit-board-${i + 1}`,
        members: [],
      }
    })

    try {
      // upload jurisdictions
      const data: Jurisdiction[] = [
        {
          id: 'jurisdiction-1',
          name: 'Jurisdiction 1',
          contests: [`contest-1`],
          auditBoards: auditBoards,
        },
      ]
      this.setState({ isLoading: true })
      await api('/audit/jurisdictions', {
        method: 'POST',
        body: JSON.stringify({ jurisdictions: data }),
        headers: {
          'Content-Type': 'application/json',
        },
      })

      // get latest audit with jurisdiction id and use it to upload the data
      let audit: any = await api('/audit/status', {})
      this.setState({ audit })
      if (audit.jurisdictions.length < 1) {
        return
      }
      const jurisdictionID: string = audit.jurisdictions[0].id

      // upload form data
      if (!manifestCSV) {
        this.setState({ audit })
        return
      }
      const formData: FormData = new FormData()
      formData.append('manifest', manifestCSV, manifestCSV.name)
      await api(`/jurisdiction/${jurisdictionID}/manifest`, {
        method: 'POST',
        body: formData,
      })

      audit = await api('/audit/status', {})
      this.setState({ audit, isLoading: false })
    } catch (err) {
      toast.error(err.message)
    }
    // TODO: Api endpoints not yet clear
  }

  public generateOptions = (count: number): JSX.Element[] => {
    let elements: JSX.Element[] = []
    for (let i = 1; i <= count; i++) {
      elements.push(<option key={i.toString()}>{i}</option>)
    }
    return elements
  }

  public downloadBallotRetrievalList = (id: number, e: any) => {
    e.preventDefault()
    const jurisdictionID: string = this.getJurisdictionId()
    window.open(`/jurisdiction/${jurisdictionID}/${id}/retrieval-list`)
  }

  public deleteBallotManifest = async (e: any) => {
    e.preventDefault()
    try {
      const jurisdictionID: string = this.state.audit.jurisdictions[0].id
      await api(`/jurisdiction/${jurisdictionID}/manifest`, {
        method: 'DELETE',
      })
      const audit: any = await api('audit/status', { method: 'GET' })
      this.setState({ audit })
    } catch (err) {
      toast.error(err.message)
    }
  }

  public calculateRiskMeasurement = async (data: any, evt: any) => {
    evt.preventDefault()
    const { id, candidateOne, candidateTwo } = data
    try {
      const jurisdictionID: string = this.state.audit.jurisdictions[0].id
      const body: any = {
        contests: [
          {
            id: 'contest-1',
            results: {
              'candidate-1': Number(candidateOne),
              'candidate-2': Number(candidateTwo),
            },
          },
        ],
      }

      this.setState({ isLoading: true })
      await api(`/jurisdiction/${jurisdictionID}/${id}/results`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      })
      const audit: any = await this.getStatus()
      this.setState({ audit, isLoading: false })
    } catch (err) {
      toast.error(err.message)
    }
  }

  public downloadAuditReport = async (i: number, round: any, evt: any) => {
    evt.preventDefault()
    try {
      window.open(`/audit/report`)
      const audit: any = await this.getStatus()
      this.setState({ audit })
    } catch (err) {
      toast.error(err.message)
    }
  }

  public inputChange(e: any): any {
    this.setState({ [e.target.name]: e.target.value })
  }

  public render() {
    const { audit, canEstimateSampleSize } = this.state
    const formOneHasData = audit && audit.contests[0]
    const formTwoHasData = audit && audit.jurisdictions[0]
    const manifestUploaded =
      formTwoHasData && audit.jurisdictions[0].ballotManifest.filename
    const formThreeHasData = manifestUploaded && audit.rounds.length > 0

    return (
      <React.Fragment>
        <EstimateSampleSize
          audit={audit}
          formOneHasData={formOneHasData}
          generateOptions={this.generateOptions}
          isLoading={this.state.isLoading}
          submitFormOne={this.submitFormOne}
          canEstimateSampleSize={canEstimateSampleSize}
        />

        <SelectBallotsToAudit
          audit={audit}
          formOneHasData={formOneHasData}
          formTwoHasData={formTwoHasData}
          formThreeHasData={formThreeHasData}
          isLoading={this.state.isLoading}
          submitFormTwo={this.submitFormTwo}
          generateOptions={this.generateOptions}
          manifestUploaded={manifestUploaded}
          fileInputChange={this.fileInputChange}
          deleteBallotManifest={this.deleteBallotManifest}
        />

        <CalculateRiskMeasurement
          audit={audit}
          isLoading={this.state.isLoading}
          downloadBallotRetrievalList={this.downloadBallotRetrievalList}
          calculateRiskMeasurement={this.calculateRiskMeasurement}
          downloadAuditReport={this.downloadAuditReport}
        />
      </React.Fragment>
    )
  }
}

export default AuditForms
