import * as Yup from 'yup'
import number from '../../../../utils/number-schema'

const schema = Yup.object().shape({
  state: Yup.string().required('Required'),
  electionName: Yup.string().required('Required'),
  randomSeed: Yup.string()
    .max(100, 'Must be 100 characters or fewer')
    .required('Required'),
  riskLimit: number()
    .typeError('Must be a number')
    .min(1, 'Must be greater than 0')
    .max(20, 'Must be less than 21')
    .required('Required'),
})

export default schema
