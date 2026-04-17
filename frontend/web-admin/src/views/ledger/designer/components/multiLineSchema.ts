export interface MultiLineInputSchema {
  controlName: string
  mappingVariable: string
  fontSizePx: number
  richText: boolean
  widthPx: number
  heightPx: number
  defaultValue: string
}

export const MULTI_LINE_INPUT_JSON_SCHEMA = {
  type: 'object',
  title: 'multi-line-input',
  properties: {
    controlName: { type: 'string', title: '控件名称' },
    mappingVariable: { type: 'string', title: '映射变量' },
    fontSizePx: { type: 'number', title: '字体大小(PX)', minimum: 10, maximum: 40 },
    richText: { type: 'boolean', title: '富文本形式' },
    widthPx: { type: 'number', title: '控件宽度(PX)', minimum: 120 },
    heightPx: { type: 'number', title: '控件高度(PX)', minimum: 60 },
    defaultValue: { type: 'string', title: '默认值' }
  },
  required: ['controlName', 'mappingVariable']
} as const
