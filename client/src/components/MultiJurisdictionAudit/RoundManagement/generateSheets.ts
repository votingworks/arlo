import jsPDF from 'jspdf'
import { IAuditBoard } from '../useAuditBoards'
import { IBallot } from './useBallots'

// Label constants in points
const LABEL_HEIGHT = 72
const LABEL_WIDTH = 190
const LABEL_START_Y = 36
const LABEL_START_X = 13
const LABEL_MARGIN_X = 9
const LABEL_PADDING_Y = 7
const LABEL_PADDING_X = 7

export const downloadLabels = (
  roundNum: number,
  ballots: IBallot[],
  jurisdictionName: string,
  auditName: string
): string => {
  if (ballots.length) {
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
      ]
        .filter(line => line)
        .map(
          line =>
            labels.splitTextToSize(line!, LABEL_WIDTH - LABEL_PADDING_X * 2)[0]
        )

      labels.text(leftX + LABEL_PADDING_X, topY + LABEL_PADDING_Y, lines, {
        baseline: 'top',
      })
    })
    labels.autoPrint()
    labels.save(
      `Round ${roundNum} Labels - ${jurisdictionName} - ${auditName}.pdf`
    )
    return labels.output() // returned for test snapshots
  }
  return ''
}

// Placeholder constants in millimeters
const PLACEHOLDERS_WIDTH = 180
const PLACEHOLDERS_START_X = 20
const PLACEHOLDERS_START_Y = 20

export const downloadPlaceholders = (
  roundNum: number,
  ballots: IBallot[],
  jurisdictionName: string,
  auditName: string
): string => {
  if (ballots.length) {
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
      ]
        .filter(line => line)
        .map(line => placeholders.splitTextToSize(line!, PLACEHOLDERS_WIDTH)[0])

      placeholders.text(lines, PLACEHOLDERS_START_X, PLACEHOLDERS_START_Y, {
        baseline: 'top',
        lineHeightFactor: 2,
      })
      pageCount += 1
    })
    placeholders.autoPrint()
    placeholders.save(
      `Round ${roundNum} Placeholders - ${jurisdictionName} - ${auditName}.pdf`
    )
    return placeholders.output() // returned for test snapshots
  }
  return ''
}

export const downloadAuditBoardCredentials = (
  auditBoards: IAuditBoard[],
  jurisdictionName: string,
  auditName: string
): string => {
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
      auditBoardCreds.setFontSize(22)
      auditBoardCreds.setFontStyle('bold')
      auditBoardCreds.text(board.name, 20, 20)
      auditBoardCreds.setFontSize(14)
      auditBoardCreds.setFontStyle('normal')
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
  auditBoardCreds.save(
    `Audit Board Credentials - ${jurisdictionName} - ${auditName}.pdf`
  )
  return auditBoardCreds.output() // returned for test snapshots
}
