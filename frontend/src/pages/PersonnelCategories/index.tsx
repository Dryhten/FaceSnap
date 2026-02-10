import { useState, useEffect } from 'react'
import { Table, Button, Space, Modal, Form, Input, InputNumber, message } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { personnelCategoriesApi } from '@/services/api'
import type { PersonnelCategory } from '@/types'

const PersonnelCategories = () => {
  const [list, setList] = useState<PersonnelCategory[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<PersonnelCategory | null>(null)
  const [form] = Form.useForm()

  const loadList = async () => {
    setLoading(true)
    try {
      const data = await personnelCategoriesApi.getList()
      setList(data || [])
    } catch (error: any) {
      message.error(error.message || '加载类别列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadList()
  }, [])

  const handleAdd = () => {
    setEditingRecord(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleEdit = (record: PersonnelCategory) => {
    setEditingRecord(record)
    form.setFieldsValue({
      name: record.name,
      sort_order: record.sort_order ?? 0,
    })
    setModalOpen(true)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingRecord) {
        await personnelCategoriesApi.update(editingRecord.id, {
          name: values.name,
          sort_order: values.sort_order,
        })
        message.success('更新成功')
      } else {
        await personnelCategoriesApi.create({
          name: values.name,
          sort_order: values.sort_order,
        })
        message.success('添加成功')
      }
      setModalOpen(false)
      form.resetFields()
      loadList()
    } catch (error: any) {
      if (error.errorFields) return
      message.error(error.message || '操作失败')
    }
  }

  const columns: ColumnsType<PersonnelCategory> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '类别名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 100,
      render: (v: number) => v ?? 0,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: unknown, record: PersonnelCategory) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加类别
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={list}
        loading={loading}
        rowKey="id"
        pagination={false}
      />
      <Modal
        title={editingRecord ? '编辑人员类别' : '添加人员类别'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setModalOpen(false)
          form.resetFields()
        }}
        okText="确定"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="类别名称"
            rules={[{ required: true, message: '请输入类别名称' }]}
          >
            <Input placeholder="请输入类别名称" />
          </Form.Item>
          <Form.Item name="sort_order" label="排序" initialValue={0}>
            <InputNumber min={0} style={{ width: '100%' }} placeholder="0" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default PersonnelCategories
