import * as Yup from 'yup'

const participantsSchema = Yup.object().shape({
  state: Yup.string().required('Required'),
  csv: Yup.mixed().required('You must upload a file'),
})

export default participantsSchema
