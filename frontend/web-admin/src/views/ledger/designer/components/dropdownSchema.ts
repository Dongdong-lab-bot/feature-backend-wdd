export interface DropdownOption {
  label: string
  value: string
  isDefault: boolean
}

export interface DropdownSchema {
  controlName: string
  linkChildName: string
  width: number
  height: number
  field: string
  options: DropdownOption[]
}

export const DEFAULT_DROPDOWN_SCHEMA: DropdownSchema = {
  controlName: '',
  linkChildName: '',
  width: 200,
  height: 1,
  field: '',
  options: [
    { label: '是', value: 'yes', isDefault: true },
    { label: '否', value: 'no', isDefault: false }
  ]
}
