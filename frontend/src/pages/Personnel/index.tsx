import { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Space,
  Input,
  Modal,
  Form,
  Upload,
  message,
  Popconfirm,
  Tag,
  Image,
  Select,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  UploadOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { personnelApi, personnelCategoriesApi } from '@/services/api'
import type { Personnel, PersonnelCreate, PersonnelUpdate, PersonnelCategory } from '@/types'

const Personnel = () => {
  const [personnelList, setPersonnelList] = useState<Personnel[]>([])
  const [categoryList, setCategoryList] = useState<PersonnelCategory[]>([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<Personnel | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    loadPersonnelList()
  }, [])

  useEffect(() => {
    personnelCategoriesApi.getList().then(setCategoryList).catch(() => {})
  }, [])

  const loadPersonnelList = async () => {
    setLoading(true)
    try {
      const response = await personnelApi.getList({
        name: searchText || undefined,
      })
      setPersonnelList(response.items || response)
    } catch (error: any) {
      message.error(error.message || '加载人员列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    loadPersonnelList()
  }

  const handleAdd = () => {
    setEditingRecord(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const handleEdit = (record: Personnel) => {
    setEditingRecord(record)
    const categoryId = record.category
      ? categoryList.find((c) => c.name === record.category)?.id ?? undefined
      : undefined
    form.setFieldsValue({
      name: record.name,
      id_number: record.id_number,
      phone: record.phone,
      address: record.address,
      gender: record.gender,
      category_id: categoryId ?? null,
    })
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await personnelApi.delete(id)
      message.success('删除成功')
      loadPersonnelList()
    } catch (error: any) {
      message.error(error.message || '删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const fileList = form.getFieldValue('photo')
      const photo = fileList?.[0]?.originFileObj

      if (editingRecord) {
        const updateData: PersonnelUpdate = {
          name: values.name,
          id_number: values.id_number,
          phone: values.phone,
          address: values.address,
          gender: values.gender,
          category_id: values.category_id ?? null,
        }
        if (photo) {
          updateData.photo = photo
        }
        await personnelApi.update(editingRecord.id, updateData)
        message.success('更新成功')
      } else {
        if (!photo) {
          message.error('请上传人员照片')
          return
        }
        const createData: PersonnelCreate = {
          name: values.name,
          id_number: values.id_number,
          phone: values.phone,
          address: values.address,
          gender: values.gender,
          category_id: values.category_id ?? null,
          photo,
        }
        await personnelApi.create(createData)
        message.success('创建成功')
      }
      setIsModalOpen(false)
      form.resetFields()
      loadPersonnelList()
    } catch (error: any) {
      if (error.errorFields) {
        // 表单验证错误
        return
      }
      message.error(error.message || '操作失败')
    }
  }

  const columns: ColumnsType<Personnel> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '照片',
      dataIndex: 'photo_path',
      key: 'photo_path',
      width: 100,
      render: (photoPath: string) => {
        if (!photoPath) return '-'
        // 使用相对路径，通过 vite 代理访问
        const imageUrl = `/api/v1/faces/${photoPath}`
        return (
          <Image
            width={50}
            height={50}
            src={imageUrl}
            style={{ objectFit: 'contain' }}
            preview={{
              mask: '预览',
            }}
            fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG4W+FgYxN"
          />
        )
      },
    },
    {
      title: '姓名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '身份证号',
      dataIndex: 'id_number',
      key: 'id_number',
    },
    {
      title: '电话',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: '住址',
      dataIndex: 'address',
      key: 'address',
    },
    {
      title: '性别',
      dataIndex: 'gender',
      key: 'gender',
      render: (gender: string) => {
        if (!gender) return '-'
        const genderMap: Record<string, string> = {
          'male': '男',
          'female': '女',
          'other': '其他',
        }
        return genderMap[gender] || gender
      },
    },
    {
      title: '人员类别',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => category || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time: string) => new Date(time).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: Personnel) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这条记录吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
        <Space>
          <Input
            placeholder="搜索姓名"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 200 }}
            onPressEnter={handleSearch}
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
            搜索
          </Button>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          添加人员
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={personnelList}
        loading={loading}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showTotal: (total) => `共 ${total} 条`,
        }}
      />

      <Modal
        title={editingRecord ? '编辑人员' : '添加人员'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="姓名"
            rules={[{ required: true, message: '请输入姓名' }]}
          >
            <Input placeholder="请输入姓名" />
          </Form.Item>
          <Form.Item
            name="id_number"
            label="身份证号"
            rules={[
              {
                pattern: /^[1-9]\d{5}(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]$/,
                message: '请输入正确的身份证号',
              },
            ]}
          >
            <Input placeholder="请输入身份证号" />
          </Form.Item>
          <Form.Item
            name="phone"
            label="电话"
            rules={[
              {
                pattern: /^1[3-9]\d{9}$/,
                message: '请输入正确的手机号',
              },
            ]}
          >
            <Input placeholder="请输入电话" />
          </Form.Item>
          <Form.Item
            name="address"
            label="住址"
          >
            <Input placeholder="请输入住址" />
          </Form.Item>
          <Form.Item
            name="gender"
            label="性别"
          >
            <Select placeholder="请选择性别" allowClear>
              <Select.Option value="male">男</Select.Option>
              <Select.Option value="female">女</Select.Option>
              <Select.Option value="other">其他</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="category_id" label="人员类别">
            <Select
              placeholder="请选择人员类别"
              allowClear
              options={categoryList.map((c) => ({ label: c.name, value: c.id }))}
            />
          </Form.Item>
          <Form.Item
            name="photo"
            label="照片"
            rules={[{ required: !editingRecord, message: '请上传照片' }]}
            valuePropName="fileList"
            getValueFromEvent={(e) => {
              if (Array.isArray(e)) {
                return e
              }
              return e?.fileList
            }}
          >
            <Upload
              listType="picture-card"
              maxCount={1}
              beforeUpload={() => false}
              accept="image/*"
            >
              <div>
                <UploadOutlined />
                <div style={{ marginTop: 8 }}>上传</div>
              </div>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Personnel

