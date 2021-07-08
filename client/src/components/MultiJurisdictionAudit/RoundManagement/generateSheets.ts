import jsPDF from 'jspdf'
import { IAuditBoard } from '../useAuditBoards'
import { getBallots } from './useBallots'
import { IRound } from '../useRoundsAuditAdmin'

// Label constants in points
const LABEL_HEIGHT = 72
const LABEL_WIDTH = 190
const LABEL_START_Y = 36
const LABEL_START_X = 13
const LABEL_MARGIN_X = 9
const LABEL_PADDING_Y = 7
const LABEL_PADDING_X = 7

export const downloadLabels = async (
  electionId: string,
  jurisdictionId: string,
  round: IRound,
  jurisdictionName: string,
  auditName: string
): Promise<string> => {
  const ballots = await getBallots(electionId, jurisdictionId, round.id)
  if (ballots && ballots.length) {
    const labels = new jsPDF({ format: 'letter', unit: 'pt' })
    labels.setFontSize(10)
    let labelCount = 0
    ballots.forEach(ballot => {
      labelCount += 1
      if (labelCount > 30) {
        labels.addPage('letter')
        labelCount = 1
      }
      const column = (labelCount - 1) % 3
      const row = Math.floor((labelCount - 1) / 3)
      const leftX = LABEL_START_X + column * (LABEL_WIDTH + LABEL_MARGIN_X)
      const topY = LABEL_START_Y + row * LABEL_HEIGHT

      // Useful for drawing the actual label boundary when testing
      // labels.roundedRect(leftX, topY, LABEL_WIDTH, LABEL_HEIGHT, 7, 7, 'S')

      const lines = [
        ballot.auditBoard!.name,
        ballot.batch.container && `Container: ${ballot.batch.container}`,
        ballot.batch.tabulator && `Tabulator: ${ballot.batch.tabulator}`,
        `Batch: ${ballot.batch.name}`,
        `Ballot Number: ${ballot.position}`,
        ballot.imprintedId !== undefined
          ? `Imprinted ID: ${ballot.imprintedId}`
          : null,
      ]
        .filter(line => line)
        .map(
          line =>
            labels.splitTextToSize(line!, LABEL_WIDTH - LABEL_PADDING_X * 2)[0]
        )

      labels.text(lines, leftX + LABEL_PADDING_X, topY + LABEL_PADDING_Y, {
        baseline: 'top',
      })
    })
    labels.autoPrint()
    await labels.save(
      `Round ${round.roundNum} Labels - ${jurisdictionName} - ${auditName}.pdf`,
      { returnPromise: true }
    )
    return labels.output() // returned for test snapshots
  }
  return ''
}

// Placeholder constants in millimeters
const PLACEHOLDERS_WIDTH = 180
const PLACEHOLDERS_START_X = 20
const PLACEHOLDERS_START_Y = 20

export const downloadPlaceholders = async (
  electionId: string,
  jurisdictionId: string,
  round: IRound,
  jurisdictionName: string,
  auditName: string
): Promise<string> => {
  const ballots = await getBallots(electionId, jurisdictionId, round.id)
  if (ballots && ballots.length) {
    const placeholders = new jsPDF({ format: 'letter' })
    placeholders.setFontSize(20)
    let pageCount = 0
    ballots.forEach(ballot => {
      if (pageCount > 0) placeholders.addPage('letter')

      const lines = [
        ballot.auditBoard!.name,
        ballot.batch.container && `Container: ${ballot.batch.container}`,
        ballot.batch.tabulator && `Tabulator: ${ballot.batch.tabulator}`,
        `Batch: ${ballot.batch.name}`,
        `Ballot Number: ${ballot.position}`,
        ballot.imprintedId !== undefined
          ? `Imprinted ID: ${ballot.imprintedId}`
          : null,
      ]
        .filter(line => line)
        .map(line => placeholders.splitTextToSize(line!, PLACEHOLDERS_WIDTH))
        .flat()

      placeholders.text(lines, PLACEHOLDERS_START_X, PLACEHOLDERS_START_Y, {
        baseline: 'top',
        lineHeightFactor: 2,
      })
      pageCount += 1
    })
    placeholders.autoPrint()
    await placeholders.save(
      `Round ${round.roundNum} Placeholders - ${jurisdictionName} - ${auditName}.pdf`,
      { returnPromise: true }
    )
    return placeholders.output() // returned for test snapshots
  }
  return ''
}

export const downloadAuditBoardCredentials = async (
  auditBoards: IAuditBoard[],
  jurisdictionName: string,
  auditName: string
): Promise<string> => {
  const auditBoardsWithoutBallots: string[] = []
  const auditBoardCreds = new jsPDF({ format: 'letter' })
  auditBoards.forEach((board, i) => {
    const qr: HTMLCanvasElement | null = document.querySelector(
      `#qr-${board.passphrase} > canvas`
    )
    /* istanbul ignore next */
    if (!qr) return
    if (board.currentRoundStatus.numSampledBallots > 0) {
      if (i > 0) auditBoardCreds.addPage('letter')
      const url = qr.toDataURL()
      auditBoardCreds.setFont('Helvetica', '', 'bold')
      auditBoardCreds.setFontSize(22)
      auditBoardCreds.text(board.name, 20, 20)
      auditBoardCreds.setFont('Helvetica', '', 'normal')
      auditBoardCreds.setFontSize(14)
      auditBoardCreds.text(
        'Scan this QR code to enter the votes you see on your assigned ballots.',
        20,
        40
      )
      auditBoardCreds.addImage(url, 'JPEG', 20, 50, 50, 50)
      auditBoardCreds.text(
        auditBoardCreds.splitTextToSize(
          'If you are not able to scan the QR code, you may also type the following URL into a web browser to access the data entry portal.',
          180
        ),
        20,
        120
      )
      const urlText: string[] = auditBoardCreds.splitTextToSize(
        `${window.location.origin}/auditboard/${board.passphrase}`,
        180
      )
      const urlHeight = urlText.reduce(
        (a: number, t: string) => auditBoardCreds.getTextDimensions(t).h + a,
        0
      )
      auditBoardCreds.text(urlText, 20, 140)
      auditBoardCreds.link(0, 130, 220, urlHeight + 10, {
        url: `${window.location.origin}/auditboard/${board.passphrase}`,
      })
    } else {
      auditBoardsWithoutBallots.push(board.name)
    }
  })
  if (auditBoardsWithoutBallots.length) {
    auditBoardCreds.addPage('letter')
    auditBoardsWithoutBallots.forEach((name, i) => {
      auditBoardCreds.text(`${name}: No ballots`, 20, i * 10 + 20)
    })
  }
  auditBoardCreds.autoPrint()
  await auditBoardCreds.save(
    `Audit Board Credentials - ${jurisdictionName} - ${auditName}.pdf`,
    { returnPromise: true }
  )
  return auditBoardCreds.output() // returned for test snapshots
}
