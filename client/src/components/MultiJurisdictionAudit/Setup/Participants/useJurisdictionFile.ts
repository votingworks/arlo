import { useEffect, useState } from 'react'
import { toast } from 'react-toastify'
import { api } from '../../../utilities'
import { IFileInfo } from '../../useJurisdictions'

const loadJurisdictionFile = async (
  electionId: string
): Promise<IFileInfo | null> => {
  try {
    return await api(`/election/${electionId}/jurisdiction/file`)
  } catch (err) /* istanbul ignore next */ {
    // TODO migrate toasting to api to consolidate testing
    toast.error(err.message)
    return null
  }
}

const putJurisdictionFileFile = async (
  electionId: string,
  csv: File
): Promise<boolean> => {
  const formData: FormData = new FormData()
  formData.append('jurisdictions', csv, csv.name)
  try {
    await api(`/election/${electionId}/jurisdiction/file`, {
      method: 'PUT',
      body: formData,
    })
    return true
  } catch (err) {
    toast.error(err.message)
    return false
  }
}

const useJurisdictionFile = (
  electionId: string
): [IFileInfo | null, (csv: File) => Promise<boolean>] => {
  const [jurisdictionFile, setJurisdictionFile] = useState<IFileInfo | null>(
    null
  )

  const uploadJurisdictionFile = async (csv: File): Promise<boolean> => {
    // TODO poll for result of upload
    if (await putJurisdictionFileFile(electionId, csv)) {
      setJurisdictionFile(await loadJurisdictionFile(electionId))
      return true
    }
    return false
  }

  useEffect(() => {
    ;(async () => {
      setJurisdictionFile(await loadJurisdictionFile(electionId))
    })()
  }, [electionId])

  return [jurisdictionFile, uploadJurisdictionFile]
}

export default useJurisdictionFile
