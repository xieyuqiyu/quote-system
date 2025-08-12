// 阀门报价系统前端 - 版本 2.0 (支持交互式选择)
console.log('🎯 前端版本: 2.0 - 支持交互式选择功能');
console.log('🕐 加载时间:', new Date().toLocaleString());

const { useState, useEffect } = React;
const { Form, Input, Button, Upload, Table, Card, message, Modal, Select, Spin, Typography, Space, Popconfirm, Tag, Tabs, Collapse, Switch, Row, Col, Progress, Divider, Radio } = antd;
const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const { Panel } = Collapse;

// API配置
const API_BASE = 'http://localhost:8001/api';

// 基础请求函数
const request = async (url, options = {}) => {
    const token = localStorage.getItem('authToken');
    if (token) {
        options.headers = {
            ...options.headers,
            'Authorization': 'Basic ' + token
        };
    }
    
    try {
        console.log(`🔍 [DEBUG] 发送请求: ${API_BASE}${url}`);
        
        // 设置请求模式为cors，确保正确处理跨域请求
        options.mode = 'cors';
        options.credentials = 'include';  // 包含凭证
        
        const response = await fetch(`${API_BASE}${url}`, options);
        
        console.log(`🔍 [DEBUG] 请求状态: ${response.status}`);
        
        if (response.status === 401) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('username');
            localStorage.removeItem('isAdmin');
            window.location.reload();
            throw new Error('请重新登录');
        }
        
        if (!response.ok) {
            console.error(`❌ [DEBUG] 请求失败: ${response.status}`);
            const text = await response.text();
            console.error(`❌ [DEBUG] 错误详情: ${text}`);
            
            try {
                const data = JSON.parse(text);
                throw new Error(data.detail || `请求失败(${response.status})`);
            } catch (e) {
                throw new Error(`请求失败: ${response.status} - ${text.substring(0, 100)}`);
            }
        }
        
        return response;
    } catch (error) {
        console.error(`❌ [DEBUG] 请求异常: ${error.message}`);
        
        // 检查是否为CORS错误
        if (error.message.includes('NetworkError') || 
            error.message.includes('Failed to fetch') ||
            error.message.includes('CORS')) {
            message.error(`服务器连接失败，请检查后端服务是否正常运行 (${error.message})`);
        } else {
            message.error(error.message);
        }
        
        throw error;
    }
};

// 登录组件
const Login = ({ onLogin }) => {
    const [loading, setLoading] = useState(false);
    
    const handleSubmit = async (values) => {
        setLoading(true);
        try {
            const token = btoa(`${values.username}:${values.password}`);
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: {
                    'Authorization': 'Basic ' + token
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('authToken', token);
                localStorage.setItem('username', data.username);
                localStorage.setItem('isAdmin', data.is_admin);
                onLogin(data);
            } else {
                message.error('用户名或密码错误');
            }
        } catch (error) {
            message.error('登录失败');
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div className="login-container">
            <div className="login-form">
                <Title level={2} style={{ textAlign: 'center', marginBottom: 32 }}>
                    阀门报价系统
                </Title>
                <Form onFinish={handleSubmit} layout="vertical">
                    <Form.Item
                        label="用户名"
                        name="username"
                        rules={[{ required: true, message: '请输入用户名' }]}
                    >
                        <Input size="large" placeholder="请输入用户名" />
                    </Form.Item>
                    <Form.Item
                        label="密码"
                        name="password"
                        rules={[{ required: true, message: '请输入密码' }]}
                    >
                        <Input.Password size="large" placeholder="请输入密码" />
                    </Form.Item>
                    <Form.Item>
                        <Button type="primary" htmlType="submit" size="large" block loading={loading}>
                            登录
                        </Button>
                    </Form.Item>
                </Form>
                <Text type="secondary" style={{ display: 'block', textAlign: 'center' }}>
                    默认管理员账号：admin / admin123
                </Text>
            </div>
        </div>
    );
};

// 账户管理组件
const AccountManagement = () => {
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [customProductModalVisible, setCustomProductModalVisible] = useState(false);
    const [cleanupLoading, setCleanupLoading] = useState(false);
    const [form] = Form.useForm();
    const [discounts, setDiscounts] = useState({}); // { username: discount }
    
    const loadAccounts = async () => {
        setLoading(true);
        try {
            const response = await request('/accounts');
            const data = await response.json();
            setAccounts(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    useEffect(() => {
        loadAccounts();
    }, []);
    
    const loadDiscountForUser = async (username) => {
        try {
            const res = await request(`/admin/user-discount?target_user=${encodeURIComponent(username)}`);
            const data = await res.json();
            setDiscounts(prev => ({ ...prev, [username]: data.discount }));
        } catch (e) {
            // ignore
        }
    };
    
    useEffect(() => {
        if (accounts && accounts.length) {
            accounts.forEach(u => loadDiscountForUser(u));
        }
    }, [accounts]);
    
    const handleSaveDiscount = async (username) => {
        const val = discounts[username];
        if (val === undefined || val === null || val === '') {
            message.warning('请输入折扣（0-1之间的小数）');
            return;
        }
        try {
            const formData = new FormData();
            formData.append('target_user', username);
            formData.append('discount', val);
            const res = await request('/admin/user-discount', { method: 'POST', body: formData });
            await res.json();
            message.success('折扣已保存');
        } catch (e) {
            message.error('折扣保存失败');
        }
    };
    
    const handleCreate = async (values) => {
        try {
            await request('/accounts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(values)
            });
            message.success('账户创建成功');
            setCustomProductModalVisible(false);
            form.resetFields();
            loadAccounts();
        } catch (error) {
            console.error(error);
        }
    };
    
    const handleDelete = async (username) => {
        try {
            await request(`/accounts/${username}`, { method: 'DELETE' });
            message.success('账户删除成功');
            loadAccounts();
        } catch (error) {
            console.error(error);
        }
    };
    
    const handleCleanupTemp = async () => {
        setCleanupLoading(true);
        try {
            console.log('🧹 [DEBUG] 开始清理所有临时文件夹');
            const response = await request('/admin/cleanup-temp', {
                method: 'POST'
            });
            
            const result = await response.json();
            console.log('✅ [DEBUG] 清理临时文件夹结果:', result);
            
            message.success(result.message);
            
            // 显示详细结果
            if (result.total_found > 0) {
                const userDetails = Object.entries(result.user_stats)
                    .filter(([_, stats]) => stats.found > 0)
                    .map(([user, stats]) => `${user}: 发现${stats.found}个, 删除${stats.deleted}个${stats.failed > 0 ? `, 失败${stats.failed}个` : ''}`)
                    .join('\n');
                
                Modal.info({
                    title: '清理临时文件夹结果',
                    content: (
                        <div>
                            <p>共发现 {result.total_found} 个临时文件夹</p>
                            <p>成功删除 {result.total_deleted} 个</p>
                            <p>失败 {result.total_failed} 个</p>
                            <Divider />
                            <p>用户详情:</p>
                            <pre style={{ maxHeight: '200px', overflow: 'auto' }}>
                                {userDetails}
                            </pre>
                        </div>
                    ),
                    width: 500,
                });
            }
        } catch (error) {
            console.error('❌ [DEBUG] 清理临时文件夹失败:', error);
            message.error(`清理临时文件夹失败: ${error.message}`);
        } finally {
            setCleanupLoading(false);
        }
    };
    
    return (
        <Card title="账户管理" extra={
            <Space>
                <Button 
                    type="default" 
                    onClick={handleCleanupTemp} 
                    loading={cleanupLoading}
                    icon={<DeleteOutlined />}
                >
                    清理临时文件
                </Button>
                <Button type="primary" onClick={() => setCustomProductModalVisible(true)}>
                    新增账户
                </Button>
            </Space>
        }>
            <Table
                loading={loading}
                dataSource={accounts.map(acc => ({ username: acc }))}
                rowKey="username"
                columns={[
                    {
                        title: '用户名',
                        dataIndex: 'username',
                        key: 'username',
                        render: (text) => (
                            <Space>
                                {text}
                                {text === 'admin' && <Tag color="gold">管理员</Tag>}
                            </Space>
                        )
                    },
                    {
                        title: '折扣',
                        key: 'discount',
                        render: (_, record) => (
                            <Space>
                                <Input
                                    style={{ width: 120 }}
                                    value={discounts[record.username] ?? ''}
                                    placeholder="0-1"
                                    onChange={(e) => {
                                        const v = e.target.value;
                                        setDiscounts(prev => ({ ...prev, [record.username]: v }));
                                    }}
                                />
                                <Button type="primary" onClick={() => handleSaveDiscount(record.username)}>保存</Button>
                            </Space>
                        )
                    },
                    {
                        title: '操作',
                        key: 'action',
                        render: (_, record) => (
                            record.username !== 'admin' && (
                                <Popconfirm
                                    title="确定删除该账户？"
                                    onConfirm={() => handleDelete(record.username)}
                                >
                                    <Button type="link" danger>删除</Button>
                                </Popconfirm>
                            )
                        )
                    }
                ]}
            />
            
            <Modal
                title="新增账户"
                open={customProductModalVisible}
                onCancel={() => {
                    setCustomProductModalVisible(false);
                    form.resetFields();
                }}
                footer={null}
            >
                <Form form={form} onFinish={handleCreate} layout="vertical">
                    <Form.Item
                        label="用户名"
                        name="username"
                        rules={[{ required: true, message: '请输入用户名' }]}
                    >
                        <Input placeholder="请输入用户名" readOnly />
                    </Form.Item>
                    <Form.Item
                        label="密码"
                        name="password"
                        rules={[{ required: true, message: '请输入密码' }]}
                    >
                        <Input.Password placeholder="请输入密码" />
                    </Form.Item>
                    <Form.Item>
                        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                            <Button onClick={() => {
                                setCustomProductModalVisible(false);
                                form.resetFields();
                            }}>
                                取消
                            </Button>
                            <Button type="primary" htmlType="submit">
                                创建
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </Card>
    );
};

// 默认规则管理组件
const DefaultRulesManagement = () => {
    const [loading, setLoading] = useState(false);
    const [options, setOptions] = useState({});
    const [rules, setRules] = useState({ product_defaults: {}, custom_products: {} });
    const [form] = Form.useForm();
    const [customProductForm] = Form.useForm();
    const [customProductModalVisible, setCustomProductModalVisible] = useState(false);
    
    const loadOptions = async () => {
        try {
            const response = await request('/default-rules/options');
            const data = await response.json();
            setOptions(data);
        } catch (error) {
            console.error(error);
        }
    };
    
    const loadRules = async () => {
        setLoading(true);
        try {
            const response = await request('/default-rules');
            const data = await response.json();
            setRules(data);
            
            // 设置表单值
            const formValues = {};
            Object.keys(data.product_defaults || {}).forEach(productType => {
                const defaults = data.product_defaults[productType];
                Object.keys(defaults).forEach(field => {
                    formValues[`${productType}_${field}`] = defaults[field];
                });
            });
            form.setFieldsValue(formValues);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    useEffect(() => {
        loadOptions();
        loadRules();
    }, []);
    
    const handleSave = async (values) => {
        try {
            const updatedRules = { ...rules };
            
            // 重新组织表单数据
            Object.keys(values).forEach(key => {
                const [productType, field] = key.split('_');
                if (!updatedRules.product_defaults[productType]) {
                    updatedRules.product_defaults[productType] = {};
                }
                updatedRules.product_defaults[productType][field] = values[key];
            });
            
            await request('/default-rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedRules)
            });
            
            message.success('默认规则保存成功');
            setRules(updatedRules);
        } catch (error) {
            console.error(error);
        }
    };
    
    const handleAddCustomProduct = async (values) => {
        try {
            const updatedRules = { ...rules };
            updatedRules.custom_products[values.code] = {
                name: values.name,
                drive_mode: values.drive_mode || "",
                connection: values.connection || "4",
                structure: values.structure || "1",
                sealing: values.sealing || "X",
                pressure: values.pressure || "16",
                material: values.material || "Q"
            };
            
            await request('/default-rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedRules)
            });
            
            message.success('自定义产品添加成功');
            setRules(updatedRules);
            setCustomProductModalVisible(false);
            customProductForm.resetFields();
        } catch (error) {
            console.error(error);
        }
    };
    
    const handleDeleteCustomProduct = async (productCode) => {
        try {
            const updatedRules = { ...rules };
            delete updatedRules.custom_products[productCode];
            
            await request('/default-rules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedRules)
            });
            
            message.success('自定义产品删除成功');
            setRules(updatedRules);
        } catch (error) {
            console.error(error);
        }
    };
    
    const renderProductDefaults = () => {
        if (!options.basic_product_types) return null;
        
        return Object.keys(options.basic_product_types).map(productType => (
            <Panel key={productType} header={`${productType} - ${options.basic_product_types[productType]}`}>
                <Row gutter={16}>
                    <Col span={12}>
                        <Form.Item
                            label="驱动方式"
                            name={`${productType}_drive_mode`}
                        >
                            <Select placeholder="选择驱动方式">
                                {Object.keys(options.drive_modes || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key === "" ? "手动（默认）" : `${key} - ${options.drive_modes[key]}`}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item
                            label="连接方式"
                            name={`${productType}_connection`}
                        >
                            <Select placeholder="选择连接方式">
                                {Object.keys(options.connection_types || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key} - {options.connection_types[key]}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item
                            label="结构形式"
                            name={`${productType}_structure`}
                        >
                            <Select placeholder="选择结构形式">
                                {Object.keys(options.structure_forms?.[productType] || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key} - {options.structure_forms[productType][key]}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item
                            label="密封材料"
                            name={`${productType}_sealing`}
                        >
                            <Select placeholder="选择密封材料">
                                {Object.keys(options.sealing_materials || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key} - {options.sealing_materials[key]}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item
                            label="压力等级"
                            name={`${productType}_pressure`}
                        >
                            <Select placeholder="选择压力等级">
                                {(options.pressure_values || []).map(value => (
                                    <Option key={value} value={value}>
                                        PN{value}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                    <Col span={12}>
                        <Form.Item
                            label="阀体材质"
                            name={`${productType}_material`}
                        >
                            <Select placeholder="选择阀体材质">
                                {Object.keys(options.body_materials || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key} - {options.body_materials[key]}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                </Row>
            </Panel>
        ));
    };
    
    const renderCustomProducts = () => {
        const customProducts = Object.keys(rules.custom_products || {});
        
        return (
            <div>
                <div style={{ marginBottom: 16 }}>
                    <Button type="primary" onClick={() => setCustomProductModalVisible(true)}>
                        添加自定义产品
                    </Button>
                </div>
                
                {customProducts.length === 0 ? (
                    <div style={{ textAlign: 'center', color: '#999', padding: 20 }}>
                        暂无自定义产品
                    </div>
                ) : (
                    customProducts.map(productCode => {
                        const product = rules.custom_products[productCode];
                        return (
                            <Card
                                key={productCode}
                                size="small"
                                title={`${productCode} - ${product.name}`}
                                extra={
                                    <Popconfirm
                                        title="确定删除该自定义产品？"
                                        onConfirm={() => handleDeleteCustomProduct(productCode)}
                                    >
                                        <Button type="link" danger size="small">删除</Button>
                                    </Popconfirm>
                                }
                                style={{ marginBottom: 8 }}
                            >
                                <Row gutter={8}>
                                    <Col span={4}>
                                        <Text type="secondary">驱动：</Text>
                                        <Text>{product.drive_mode || "手动"}</Text>
                                    </Col>
                                    <Col span={4}>
                                        <Text type="secondary">连接：</Text>
                                        <Text>{product.connection}</Text>
                                    </Col>
                                    <Col span={4}>
                                        <Text type="secondary">结构：</Text>
                                        <Text>{product.structure}</Text>
                                    </Col>
                                    <Col span={4}>
                                        <Text type="secondary">密封：</Text>
                                        <Text>{product.sealing}</Text>
                                    </Col>
                                    <Col span={4}>
                                        <Text type="secondary">压力：</Text>
                                        <Text>PN{product.pressure}</Text>
                                    </Col>
                                    <Col span={4}>
                                        <Text type="secondary">材质：</Text>
                                        <Text>{product.material}</Text>
                                    </Col>
                                </Row>
                            </Card>
                        );
                    })
                )}
            </div>
        );
    };
    
    return (
        <Card title="默认规则管理">
            <Spin spinning={loading}>
                <Tabs defaultActiveKey="1">
                    <TabPane tab="基础产品默认规则" key="1">
                        <Form form={form} onFinish={handleSave} layout="vertical">
                            <Collapse>
                                {renderProductDefaults()}
                            </Collapse>
                            <Form.Item style={{ marginTop: 24 }}>
                                <Button type="primary" htmlType="submit" size="large">
                                    保存默认规则
                                </Button>
                            </Form.Item>
                        </Form>
                    </TabPane>
                    <TabPane tab="自定义产品管理" key="2">
                        {renderCustomProducts()}
                    </TabPane>
                </Tabs>
            </Spin>
            
            <Modal
                title="新增自定义产品"
                open={customProductModalVisible}
                onCancel={() => {
                    setCustomProductModalVisible(false);
                    customProductForm.resetFields();
                }}
                footer={null}
            >
                <Form form={customProductForm} onFinish={handleAddCustomProduct} layout="vertical">
                    <Form.Item
                        label="产品代码"
                        name="code"
                        rules={[{ required: true, message: '请输入产品代码' }]}
                    >
                        <Input placeholder="例如：DN100-PN16-Q" />
                    </Form.Item>
                    <Form.Item
                        label="产品名称"
                        name="name"
                        rules={[{ required: true, message: '请输入产品名称' }]}
                    >
                        <Input placeholder="例如：DN100 球阀" />
                    </Form.Item>
                    <Form.Item
                        label="驱动方式"
                        name="drive_mode"
                        rules={[{ required: true, message: '请选择驱动方式' }]}
                    >
                        <Select placeholder="选择驱动方式">
                            {Object.keys(options.drive_modes || {}).map(key => (
                                <Option key={key} value={key}>
                                    {key === "" ? "手动（默认）" : `${key} - ${options.drive_modes[key]}`}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        label="连接方式"
                        name="connection"
                        rules={[{ required: true, message: '请选择连接方式' }]}
                    >
                        <Select placeholder="选择连接方式">
                            {Object.keys(options.connection_types || {}).map(key => (
                                <Option key={key} value={key}>
                                    {key} - {options.connection_types[key]}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        label="结构形式"
                        name="structure"
                        rules={[{ required: true, message: '请选择结构形式' }]}
                    >
                        <Select placeholder="选择结构形式">
                            {Object.keys(options.structure_forms || {}).map(key => (
                                <Option key={key} value={key}>
                                    {key} - {options.structure_forms[key]}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        label="密封材料"
                        name="sealing"
                        rules={[{ required: true, message: '请选择密封材料' }]}
                    >
                        <Select placeholder="选择密封材料">
                            {Object.keys(options.sealing_materials || {}).map(key => (
                                <Option key={key} value={key}>
                                    {key} - {options.sealing_materials[key]}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        label="压力等级"
                        name="pressure"
                        rules={[{ required: true, message: '请选择压力等级' }]}
                    >
                        <Select placeholder="选择压力等级">
                            {(options.pressure_values || []).map(value => (
                                <Option key={value} value={value}>
                                    PN{value}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item
                        label="阀体材质"
                        name="material"
                        rules={[{ required: true, message: '请选择阀体材质' }]}
                    >
                        <Select placeholder="选择阀体材质">
                            {Object.keys(options.body_materials || {}).map(key => (
                                <Option key={key} value={key}>
                                    {key} - {options.body_materials[key]}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item>
                        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                            <Button onClick={() => {
                                setCustomProductModalVisible(false);
                                customProductForm.resetFields();
                            }}>
                                取消
                            </Button>
                            <Button type="primary" htmlType="submit">
                                创建
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </Card>
    );
};

// 交互式匹配组件
const InteractiveMatching = ({ valveInfo, onComplete, onCancel }) => {
    const [loading, setLoading] = useState(false);
    const [options, setOptions] = useState({});
    const [form] = Form.useForm();
    
    useEffect(() => {
        loadOptions();
    }, [valveInfo]);
    
    const loadOptions = async () => {
        setLoading(true);
        try {
            const response = await request('/api/get-interactive-options', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(valveInfo)
            });
            const data = await response.json();
            setOptions(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    
    const handleSubmit = async (values) => {
        try {
            const response = await request('/api/interactive-match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    valve_info: valveInfo,
                    selections: values
                })
            });
            const data = await response.json();
            message.success('匹配完成');
            onComplete(data.valve_info);
        } catch (error) {
            console.error(error);
        }
    };
    
    return (
        <Modal
            title="交互式参数选择"
            open={true}
            onCancel={onCancel}
            footer={null}
            width={800}
        >
            <Spin spinning={loading}>
                <div style={{ marginBottom: 16 }}>
                    <Text type="secondary">
                        检测到阀门信息不完整，请选择缺失的参数：
                    </Text>
                </div>
                
                <Form form={form} onFinish={handleSubmit} layout="vertical">
                    <Row gutter={16}>
                        {!valveInfo.drive_mode && (
                            <Col span={12}>
                                <Form.Item label="驱动方式" name="drive_mode">
                                    <Select placeholder="选择驱动方式">
                                        {Object.keys(options.drive_modes || {}).map(key => (
                                            <Option key={key} value={key}>
                                                {key === "" ? "手动（默认）" : `${key} - ${options.drive_modes[key]}`}
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                        )}
                        
                        {!valveInfo.connection && (
                            <Col span={12}>
                                <Form.Item label="连接方式" name="connection">
                                    <Select placeholder="选择连接方式">
                                        {Object.keys(options.connection_types || {}).map(key => (
                                            <Option key={key} value={key}>
                                                {key} - {options.connection_types[key]}
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                        )}
                        
                        {!valveInfo.structure && (
                            <Col span={12}>
                                <Form.Item label="结构形式" name="structure">
                                    <Select placeholder="选择结构形式">
                                        {Object.keys(options.structure_forms || {}).map(key => (
                                            <Option key={key} value={key}>
                                                {key} - {options.structure_forms[key]}
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                        )}
                        
                        {!valveInfo.sealing && (
                            <Col span={12}>
                                <Form.Item label="密封材料" name="sealing">
                                    <Select placeholder="选择密封材料">
                                        {Object.keys(options.sealing_materials || {}).map(key => (
                                            <Option key={key} value={key}>
                                                {key} - {options.sealing_materials[key]}
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                        )}
                        
                        {!valveInfo.pressure && (
                            <Col span={12}>
                                <Form.Item label="压力等级" name="pressure">
                                    <Select placeholder="选择压力等级">
                                        {(options.pressure_values || []).map(value => (
                                            <Option key={value} value={value}>
                                                PN{value}
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                        )}
                        
                        {!valveInfo.material && (
                            <Col span={12}>
                                <Form.Item label="阀体材质" name="material">
                                    <Select placeholder="选择阀体材质">
                                        {Object.keys(options.body_materials || {}).map(key => (
                                            <Option key={key} value={key}>
                                                {key} - {options.body_materials[key]}
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                        )}
                    </Row>
                    
                    <Form.Item>
                        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                            <Button onClick={onCancel}>取消</Button>
                            <Button type="primary" htmlType="submit">
                                确认选择
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Spin>
        </Modal>
    );
};

// 交互式流程控制组件
const InteractiveQuoteFlow = ({ priceFile, inquiryFile, company, onComplete, onCancel }) => {
    const [batchData, setBatchData] = useState(null);
    const [currentItem, setCurrentItem] = useState(null);
    const [progress, setProgress] = useState({ current: 0, total: 0 });
    const [loading, setLoading] = useState(false);
    const [step, setStep] = useState('analyzing'); // analyzing, selecting, completing
    
    useEffect(() => {
        startInteractiveFlow();
    }, []);
    
    const startInteractiveFlow = async () => {
        console.log('🚀 [DEBUG] startInteractiveFlow 被调用');
        console.log('🚀 [DEBUG] priceFile:', priceFile);
        console.log('🚀 [DEBUG] inquiryFile:', inquiryFile);
        console.log('🚀 [DEBUG] company:', company);
        
        setLoading(true);
        setStep('analyzing');
        
        try {
            const formData = new FormData();
            formData.append('price_file', priceFile);
            formData.append('inquiry_file', inquiryFile);
            formData.append('company', company); // 传递公司名
            
            console.log('🚀 [DEBUG] 即将调用 /start-interactive-quote 接口');
            
            // 使用更安全的请求方式
            const response = await fetch(`${API_BASE}/api/start-interactive-quote`, {
                method: 'POST',
                body: formData,
                mode: 'cors',
                credentials: 'include',
                headers: {
                    'Authorization': 'Basic ' + localStorage.getItem('authToken')
                }
            });
            
            console.log('🚀 [DEBUG] 接口返回状态:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('🚨 [DEBUG] 接口返回错误:', response.status, errorText);
                throw new Error(`接口返回错误: ${response.status} ${errorText.substring(0, 100)}`);
            }
            
            const data = await response.json();
            console.log('🚀 [DEBUG] 接口返回数据:', data);
            
            if (!data) {
                console.error('🚨 [DEBUG] 接口返回空数据');
                throw new Error('接口返回空数据');
            }
            
            if (!data.need_interaction) {
                // 无需交互，直接完成
                console.log('🚀 [DEBUG] 无需交互，直接完成');
                message.info(data.message || '无需交互，直接完成');
                await completeQuote(data.batch_id);
                return;
            }
            
            // 需要交互选择
            console.log('🚀 [DEBUG] 需要交互选择');
            console.log('🚀 [DEBUG] 批次ID:', data.batch_id);
            console.log('🚀 [DEBUG] 当前项目:', data.current_item);
            console.log('🚀 [DEBUG] 进度:', data.progress);
            
            setBatchData(data);
            setCurrentItem(data.current_item);
            setProgress(data.progress || { current: 1, total: 1 });
            setStep('selecting');
            
        } catch (error) {
            console.error('🚨 [DEBUG] 启动交互式流程失败:', error);
            
            // 特殊处理CORS错误
            if (error.message.includes('NetworkError') || 
                error.message.includes('Failed to fetch') ||
                error.message.includes('CORS') ||
                error.message.includes('Load failed')) {
                message.error(`服务器连接失败，请检查后端服务是否正常运行。可能需要重启后端服务器。`);
            } else {
                message.error(`启动交互式流程失败: ${error.message}`);
            }
            
            onCancel();
        } finally {
            setLoading(false);
        }
    };
    
    const handleParameterSubmit = async (selections) => {
        setLoading(true);
        
        try {
            console.log('🚀 [DEBUG] 提交参数选择:', selections);
            console.log('🚀 [DEBUG] 批次ID:', batchData.batch_id);
            console.log('🚀 [DEBUG] 项目索引:', currentItem.index);
            
            const response = await fetch(`${API_BASE}/api/submit-interactive-selection`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': 'Basic ' + localStorage.getItem('authToken')
                },
                body: JSON.stringify({
                    batch_id: batchData.batch_id,
                    item_index: currentItem.index,
                    selections: selections
                }),
                mode: 'cors',
                credentials: 'include'
            });
            
            console.log('🚀 [DEBUG] 提交参数选择响应状态:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('🚨 [DEBUG] 提交参数选择失败:', response.status, errorText);
                throw new Error(`提交参数选择失败: ${response.status} ${errorText.substring(0, 100)}`);
            }
            
            const data = await response.json();
            console.log('🚀 [DEBUG] 提交参数选择返回数据:', data);
            
            if (data.completed) {
                // 所有交互完成，开始生成报价
                message.success(`所有参数选择完成！共完成 ${data.total_selections} 个产品的参数选择`);
                setStep('completing');
                await completeQuote(batchData.batch_id);
            } else {
                // 继续下一个产品
                setCurrentItem(data.next_item);
                setProgress(data.progress || { current: progress.current + 1, total: progress.total });
                const newProgress = data.progress || { current: progress.current + 1, total: progress.total };
                message.success(`第 ${newProgress.current} 个产品参数选择完成`);
            }
            
        } catch (error) {
            console.error('🚨 [DEBUG] 提交参数选择失败:', error);
            
            // 特殊处理CORS错误
            if (error.message.includes('NetworkError') || 
                error.message.includes('Failed to fetch') ||
                error.message.includes('CORS') ||
                error.message.includes('Load failed')) {
                message.error(`服务器连接失败，请检查后端服务是否正常运行。可能需要重启后端服务器。`);
            } else {
                message.error(`提交参数选择失败: ${error.message}`);
            }
        } finally {
            setLoading(false);
        }
    };
    
    const completeQuote = async (batchId) => {
        setLoading(true);
        setStep('completing');
        
        try {
            console.log('🚀 [DEBUG] 完成交互式报价:', batchId);
            
            const formData = new FormData();
            formData.append('batch_id', batchId);
            
            const response = await fetch(`${API_BASE}/api/complete-interactive-quote`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': 'Basic ' + localStorage.getItem('authToken')
                },
                mode: 'cors',
                credentials: 'include'
            });
            
            console.log('🚀 [DEBUG] 完成交互式报价响应状态:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('🚨 [DEBUG] 完成交互式报价失败:', response.status, errorText);
                throw new Error(`完成交互式报价失败: ${response.status} ${errorText.substring(0, 100)}`);
            }
            
            const data = await response.json();
            console.log('🚀 [DEBUG] 完成交互式报价返回数据:', data);
            
            message.success(`交互式报价单生成成功！生成了 ${data.files ? data.files.length : 0} 个文件`);
            onComplete(data);
            
        } catch (error) {
            console.error('🚨 [DEBUG] 完成交互式报价失败:', error);
            
            // 特殊处理CORS错误
            if (error.message.includes('NetworkError') || 
                error.message.includes('Failed to fetch') ||
                error.message.includes('CORS') ||
                error.message.includes('Load failed')) {
                message.error(`服务器连接失败，请检查后端服务是否正常运行。可能需要重启后端服务器。`);
            } else {
                message.error(`完成交互式报价失败: ${error.message}`);
            }
            
            onCancel();
        } finally {
            setLoading(false);
        }
    };
    
    const renderStepContent = () => {
        if (step === 'analyzing') {
            return (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>
                        <Text>正在分析询价表，识别需要交互选择的产品...</Text>
                    </div>
                </div>
            );
        }
        
        if (step === 'selecting' && currentItem) {
            const currentProgress = progress || { current: 0, total: 0 };
            
            return (
                <div>
                    <div style={{ marginBottom: 24 }}>
                        <Progress 
                            percent={Math.round((currentProgress.current / currentProgress.total) * 100)} 
                            format={() => `${currentProgress.current}/${currentProgress.total}`}
                        />
                        <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                            正在处理第 {currentProgress.current} 个产品，共 {currentProgress.total} 个需要参数选择
                        </Text>
                    </div>
                    
                    <ProductInfoCard product={currentItem} />
                    
                    <ParameterSelectionForm 
                        product={currentItem}
                        onSubmit={handleParameterSubmit}
                        loading={loading}
                    />
                </div>
            );
        }
        
        if (step === 'completing') {
            return (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: 16 }}>
                        <Text>正在生成报价单，请稍候...</Text>
                    </div>
                </div>
            );
        }
        
        return null;
    };
    
    return (
        <Modal
            title="交互式参数选择"
            open={true}
            onCancel={onCancel}
            footer={null}
            width={900}
            closable={step !== 'completing'}
            maskClosable={false}
        >
            {renderStepContent()}
        </Modal>
    );
};

// 产品信息卡片组件
const ProductInfoCard = ({ product }) => (
    <Card size="small" style={{ marginBottom: 16, backgroundColor: '#f8f9fa' }}>
        <Row gutter={16}>
            <Col span={8}>
                <Text strong>产品名称：</Text>
                <Text>{product.name}</Text>
            </Col>
            <Col span={8}>
                <Text strong>规格型号：</Text>
                <Text>{product.specs}</Text>
            </Col>
            <Col span={8}>
                <Text strong>数量：</Text>
                <Text>{product.quantity || '-'}</Text>
            </Col>
        </Row>
        <div style={{ marginTop: 12 }}>
            <Text strong>缺失参数：</Text>
            <div style={{ marginTop: 4 }}>
                {product.missing_params.map(param => {
                    const paramNames = {
                        'drive_mode': '驱动方式',
                        'connection': '连接方式', 
                        'structure': '结构形式',
                        'sealing': '密封材料'
                    };
                    return (
                        <Tag key={param} color="orange" style={{ marginBottom: 4 }}>
                            {paramNames[param] || param}
                        </Tag>
                    );
                })}
            </div>
        </div>
    </Card>
);

// 参数选择表单组件
const ParameterSelectionForm = ({ product, onSubmit, loading }) => {
    const [form] = Form.useForm();
    const [options, setOptions] = useState({
        drive_modes: {},
        connection_types: {},
        structure_forms: {},
        sealing_materials: {},
        pressure_values: []
    });
    const [loadingOptions, setLoadingOptions] = useState(true);
    
    useEffect(() => {
        loadOptions();
    }, [product]);
    
    const loadOptions = async () => {
        setLoadingOptions(true);
        console.log('🔍 [DEBUG] 加载参数选项: valve_info=', product.valve_info);
        
        try {
            const response = await request('/api/get-interactive-options', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(product.valve_info)
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('🚨 [DEBUG] 获取选项失败:', response.status, errorText);
                throw new Error(`获取选项失败: ${response.status} ${errorText}`);
            }
            
            const data = await response.json();
            console.log('🔍 [DEBUG] 获取到选项:', data);
            setOptions(data || {
                drive_modes: {},
                connection_types: {},
                structure_forms: {},
                sealing_materials: {},
                pressure_values: []
            });
        } catch (error) {
            console.error('🚨 [DEBUG] 获取选项失败:', error);
            message.error(`获取选项失败: ${error.message}`);
        } finally {
            setLoadingOptions(false);
        }
    };
    
    const handleSubmit = async (values) => {
        // 只提交缺失的参数
        const selections = {};
        product.missing_params.forEach(param => {
            if (values[param] !== undefined) {
                selections[param] = values[param];
            }
        });
        
        await onSubmit(selections);
        form.resetFields();
    };
    
    if (loadingOptions) {
        return (
            <div style={{ textAlign: 'center', padding: 20 }}>
                <Spin />
                <div style={{ marginTop: 8 }}>加载参数选项...</div>
            </div>
        );
    }
    
    return (
        <Form form={form} onFinish={handleSubmit} layout="vertical">
            <Row gutter={16}>
                {product.missing_params.includes('drive_mode') && (
                    <Col span={12}>
                        <Form.Item 
                            label="驱动方式" 
                            name="drive_mode"
                            rules={[{ required: true, message: '请选择驱动方式' }]}
                        >
                            <Select placeholder="选择驱动方式">
                                {Object.keys(options.drive_modes || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key === "" ? "手动（默认）" : `${key} - ${options.drive_modes[key]}`}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                )}
                
                {product.missing_params.includes('connection') && (
                    <Col span={12}>
                        <Form.Item 
                            label="连接方式" 
                            name="connection"
                            rules={[{ required: true, message: '请选择连接方式' }]}
                        >
                            <Select placeholder="选择连接方式">
                                {Object.keys(options.connection_types || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key} - {options.connection_types[key]}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                )}
                
                {product.missing_params.includes('structure') && (
                    <Col span={12}>
                        <Form.Item 
                            label="结构形式" 
                            name="structure"
                            rules={[{ required: true, message: '请选择结构形式' }]}
                        >
                            <Select placeholder="选择结构形式">
                                {Object.keys(options.structure_forms || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key} - {options.structure_forms[key]}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                )}
                
                {product.missing_params.includes('sealing') && (
                    <Col span={12}>
                        <Form.Item 
                            label="密封材料" 
                            name="sealing"
                            rules={[{ required: true, message: '请选择密封材料' }]}
                        >
                            <Select placeholder="选择密封材料">
                                {Object.keys(options.sealing_materials || {}).map(key => (
                                    <Option key={key} value={key}>
                                        {key} - {options.sealing_materials[key]}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                )}
                
                {product.missing_params.includes('pressure') && (
                    <Col span={12}>
                        <Form.Item 
                            label="压力等级" 
                            name="pressure"
                            rules={[{ required: true, message: '请选择压力等级' }]}
                        >
                            <Select placeholder="选择压力等级">
                                {(options.pressure_values || []).map(value => (
                                    <Option key={value} value={value}>
                                        PN{value}
                                    </Option>
                                ))}
                            </Select>
                        </Form.Item>
                    </Col>
                )}
            </Row>
            
            <Form.Item style={{ marginTop: 24 }}>
                <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                    <Button type="primary" htmlType="submit" loading={loading}>
                        {loading ? '处理中...' : '确认选择'}
                    </Button>
                </Space>
            </Form.Item>
        </Form>
    );
};

// 文件上传组件
const FileUpload = ({ type, onSuccess, onBrandsExtracted }) => {
    const [uploading, setUploading] = useState(false);
    
    const uploadProps = {
        name: 'file',
        action: `${API_BASE}/upload/${type}`,
        headers: {
            'Authorization': 'Basic ' + localStorage.getItem('authToken')
        },
        accept: type === 'price' ? '.xlsx,.xls' : '.xlsx,.xls,.csv,.pdf,.docx,.png,.jpg,.jpeg',
        beforeUpload: (file) => {
            if (type === 'price') {
                // 价格表只支持Excel格式
                const isValidType = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');
                if (!isValidType) {
                    message.error('价格表只支持Excel文件格式(.xlsx, .xls)！');
                    return false;
                }
            } else {
                // 其他文件类型
                const isValidType = file.name.endsWith('.xlsx') || file.name.endsWith('.xls') || file.name.endsWith('.csv') || file.name.endsWith('.pdf') || file.name.endsWith('.docx') || file.name.endsWith('.png') || file.name.endsWith('.jpg') || file.name.endsWith('.jpeg');
                if (!isValidType) {
                    message.error('只能上传 Excel、CSV、PDF、Word 或图片文件！');
                    return false;
                }
            }
            return true;
        },
        onChange: (info) => {
            if (info.file.status === 'uploading') {
                setUploading(true);
                message.loading('正在验证文件格式...', 0);
            }
            if (info.file.status === 'done') {
                message.destroy();
                
                // 检查响应数据
                if (info.file.response) {
                    if (type === 'price' && info.file.response.brands) {
                        // 价格表上传成功，显示品牌信息
                        const brandCount = info.file.response.brands.length;
                        if (brandCount > 0) {
                            message.success(`${info.file.name} 上传成功！找到 ${brandCount} 个品牌: ${info.file.response.brands.join(', ')}`);
                            // 调用品牌提取回调
                            if (onBrandsExtracted) {
                                onBrandsExtracted(info.file.name, info.file.response.brands);
                            }
                        } else {
                            message.success(`${info.file.name} 上传成功！`);
                        }
                    } else {
                        message.success(`${info.file.name} 上传成功`);
                    }
                } else {
                    message.success(`${info.file.name} 上传成功`);
                }
                
                setUploading(false);
                onSuccess && onSuccess();
            } else if (info.file.status === 'error') {
                message.destroy();
                
                // 显示详细的错误信息
                let errorMsg = `${info.file.name} 上传失败`;
                if (info.file.response && info.file.response.detail) {
                    errorMsg = info.file.response.detail;
                }
                
                message.error(errorMsg);
                setUploading(false);
            }
        }
    };
    
    return (
        <Upload.Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
            </p>
            <p className="ant-upload-text">
                点击或拖拽文件到此区域上传
            </p>
            <p className="ant-upload-hint">
                {type === 'price' 
                    ? '价格表必须包含：产品名称、型号、规格、单价、品牌 5个固定字段'
                    : '支持 Excel (.xlsx, .xls)、CSV、PDF、Word、图片（.png, .jpg, .jpeg）文件'
                }
            </p>
        </Upload.Dragger>
    );
};

// 文件列表组件
const FileList = ({ files, type, onRefresh }) => {
    const handleDownload = async (filename) => {
        try {
            const token = localStorage.getItem('authToken');
            if (!token) {
                message.error('请先登录');
                return;
            }
            
            const response = await fetch(`${API_BASE}/download/${type}/${filename}`, {
                method: 'GET',
                headers: {
                    'Authorization': 'Basic ' + token
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '下载失败');
            }
            
            // 获取文件内容
            const blob = await response.blob();
            
            // 创建下载链接
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // 清理 URL 对象
            window.URL.revokeObjectURL(url);
            
            message.success('文件下载成功');
        } catch (error) {
            console.error('下载失败:', error);
            message.error(error.message || '下载失败');
            
            // 如果是文件不存在错误，自动刷新文件列表
            if (error.message && error.message.includes('文件不存在')) {
                message.info('正在刷新文件列表...');
                setTimeout(() => {
                    onRefresh && onRefresh();
                }, 1000);
            }
        }
    };
    
    return (
        <div className="file-list">
            <div style={{ marginBottom: 16, textAlign: 'right' }}>
                <Button 
                    type="link" 
                    onClick={() => onRefresh && onRefresh()}
                    style={{ padding: 0 }}
                >
                    🔄 刷新列表
                </Button>
            </div>
            {files.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 20, color: '#999' }}>
                    暂无文件
                </div>
            ) : (
                files.map(file => (
                    <div key={file} className="file-item">
                        <span>{file}</span>
                        <Button type="link" onClick={() => handleDownload(file)}>
                            下载
                        </Button>
                    </div>
                ))
            )}
        </div>
    );
};

// 报价生成组件
const QuoteGenerator = ({ priceFiles, inquiryFiles, onSuccess, uploadedBrands }) => {
    const [form] = Form.useForm();
    const [generating, setGenerating] = useState(false);
    const [useDefaultRules, setUseDefaultRules] = useState(true);
    const [interactiveFlowVisible, setInteractiveFlowVisible] = useState(false);
    const [currentQuoteParams, setCurrentQuoteParams] = useState(null);
    const [brandList, setBrandList] = useState([]);
    const [selectedBrand, setSelectedBrand] = useState(null);
    const [userPriceTable, setUserPriceTable] = useState(null);
    const [scheme, setScheme] = useState('scheme1'); // 方案选择：scheme1/ scheme2/ both
    const [showScheme2Modal, setShowScheme2Modal] = useState(false);
    const [scheme2Form] = Form.useForm();
    
    // 加载用户的价格表和品牌信息
    const loadUserPriceTableAndBrands = async () => {
        try {
            const response = await request('/files');
            const data = await response.json();
            const priceFiles = data.price_tables || [];
            
            if (priceFiles.length > 0) {
                const filename = priceFiles[0];
                setUserPriceTable(filename);
                
                // 从价格表中提取品牌信息
                try {
                    const priceResponse = await request(`/price-table/${encodeURIComponent(filename)}`);
                    const priceData = await priceResponse.json();
                    
                    // 提取品牌信息
                    const brandColumnIndex = priceData.columns.findIndex(col => 
                        col === '品牌' || col.includes('品牌') || col.includes('厂商') || col.includes('厂家')
                    );
                    
                    if (brandColumnIndex !== -1) {
                        const brandSet = new Set();
                        priceData.data.forEach(row => {
                            if (row[brandColumnIndex] && row[brandColumnIndex].toString().trim()) {
                                brandSet.add(row[brandColumnIndex].toString().trim());
                            }
                        });
                        const brands = Array.from(brandSet).sort();
                        setBrandList(brands);
                        if (brands.length > 0) {
                            message.success(`已从价格表中加载 ${brands.length} 个品牌: ${brands.join(', ')}`);
                        }
                    } else {
                        setBrandList([]);
                        message.warning('价格表中没有找到品牌列');
                    }
                } catch (error) {
                    console.error('获取价格表品牌信息失败:', error);
                    setBrandList([]);
                }
            } else {
                setUserPriceTable(null);
                setBrandList([]);
                message.warning('您还没有上传价格表，请先在"文件管理"页面上传价格表');
            }
        } catch (error) {
            console.error('加载用户价格表失败:', error);
            message.error('加载价格表失败');
        }
    };
    
    const handleGenerate = async (values) => {
        console.log('🔧 [DEBUG] handleGenerate 被调用');
        console.log('🔧 [DEBUG] useDefaultRules:', useDefaultRules);
        console.log('🔧 [DEBUG] values:', values);
        
        if (!userPriceTable) {
            message.warning('请先上传价格表');
            return;
        }
        
        if (!selectedBrand) {
            message.warning('请先选择品牌');
            return;
        }
        
        // 从价格表文件名中提取公司名，例如 "公司A.xlsx" -> "公司A"
        const company = userPriceTable.replace(/\.(xlsx|xls|csv)$/i, '');
        
        if (!useDefaultRules) {
            // 交互式选择模式
            console.log('🔧 [DEBUG] 进入交互式选择模式');
            setCurrentQuoteParams({
                price_file: userPriceTable,
                inquiry_file: values.inquiry_file,
                company: company // 传递推断出的公司名
            });
            setInteractiveFlowVisible(true);
            return;
        }
        
        // 如果是第二方案，显示对话框让用户输入信息
        if (scheme === 'scheme2') {
            console.log('🔧 [DEBUG] 进入第二方案模式，显示对话框');
            setShowScheme2Modal(true);
            return;
        }
        
        // 默认规则模式
        console.log('🔧 [DEBUG] 进入默认规则模式');
        setGenerating(true);
        try {
            const formData = new FormData();
            formData.append('price_file', userPriceTable);
            formData.append('inquiry_file', values.inquiry_file);
            formData.append('brand', selectedBrand);
            formData.append('use_default_rules', useDefaultRules);
            formData.append('company', company); // 传递推断出的公司名
            formData.append('scheme', scheme);
            
            const response = await request('/generate-quote', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            message.success('价格后报价单生成成功！');
            form.resetFields();
            
            // 延迟刷新文件列表，确保后端文件已完全写入
            setTimeout(() => {
                onSuccess && onSuccess();
            }, 1000);
        } catch (error) {
            console.error(error);
        } finally {
            setGenerating(false);
        }
    };
    
    const handleInteractiveComplete = (result) => {
        setInteractiveFlowVisible(false);
        setCurrentQuoteParams(null);
        form.resetFields();
        
        // 延迟刷新文件列表
        setTimeout(() => {
            onSuccess && onSuccess();
        }, 1000);
    };
    
    const handleInteractiveCancel = () => {
        setInteractiveFlowVisible(false);
        setCurrentQuoteParams(null);
    };
    
    // 处理第二方案对话框确认
    const handleScheme2Confirm = async (values) => {
        console.log('🔧 [DEBUG] 第二方案对话框确认:', values);
        setGenerating(true);
        setShowScheme2Modal(false);
        
        try {
            const formData = new FormData();
            formData.append('price_file', userPriceTable);
            formData.append('inquiry_file', form.getFieldValue('inquiry_file'));
            formData.append('brand', selectedBrand);
            formData.append('use_default_rules', useDefaultRules);
            formData.append('company', values.company_name);
            formData.append('scheme', 'scheme2');
            
            // 添加公司信息
            formData.append('company_name', values.company_name);
            formData.append('business_contact', values.business_contact);
            formData.append('contact_phone', values.contact_phone);
            formData.append('contact_email', values.contact_email);
            formData.append('customer_header', values.customer_header);
            formData.append('recipient', values.recipient);
            formData.append('contact_method', values.contact_method);
            formData.append('address', values.address);
            formData.append('tax_rate', values.tax_rate);
            
            const response = await request('/generate-quote', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            message.success('第二方案报价单生成成功！');
            form.resetFields();
            scheme2Form.resetFields();
            
            // 延迟刷新文件列表，确保后端文件已完全写入
            setTimeout(() => {
                onSuccess && onSuccess();
            }, 1000);
        } catch (error) {
            console.error(error);
        } finally {
            setGenerating(false);
        }
    };
    
    // 处理第二方案对话框取消
    const handleScheme2Cancel = () => {
        setShowScheme2Modal(false);
        scheme2Form.resetFields();
    };
    
    // 组件加载时获取用户价格表和品牌信息
    useEffect(() => {
        loadUserPriceTableAndBrands();
    }, []);

    return (
        <Card title="生成报价单">
            <Form form={form} onFinish={handleGenerate} layout="vertical">
                {/* 价格表信息显示 */}
                <Form.Item label="价格表">
                    {userPriceTable ? (
                        <div style={{ padding: '8px 12px', backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '6px' }}>
                            <strong>📄 {userPriceTable}</strong>
                            <Button 
                                type="link" 
                                size="small" 
                                onClick={loadUserPriceTableAndBrands}
                                style={{ marginLeft: 8 }}
                            >
                                🔄 刷新
                            </Button>
                        </div>
                    ) : (
                        <div style={{ padding: '8px 12px', backgroundColor: '#fff2e8', border: '1px solid #ffbb96', borderRadius: '6px', color: '#d46b08' }}>
                            ⚠️ 请先在"文件管理"页面上传价格表
                        </div>
                    )}
                </Form.Item>
                
                <Form.Item
                    label="选择品牌"
                    name="brand"
                    rules={[{ required: true, message: '请选择品牌' }]}
                    extra={brandList.length > 0 ? `共找到 ${brandList.length} 个品牌` : '请先上传价格表'}
                >
                    <Select
                        placeholder={brandList.length === 0 ? "请先上传价格表" : "请选择品牌"}
                        value={selectedBrand}
                        onChange={(value) => {
                            console.log('🔧 [DEBUG] 品牌选择改变:', value);
                            setSelectedBrand(value);
                        }}
                        style={{ width: 300 }}
                        disabled={brandList.length === 0}
                        notFoundContent={brandList.length === 0 ? "请先上传价格表" : "没有找到匹配的品牌"}
                    >
                        {brandList.map(brand => (
                            <Option key={brand} value={brand}>{brand}</Option>
                        ))}
                    </Select>
                </Form.Item>
                
                <Form.Item
                    label="选择询价表"
                    name="inquiry_file"
                    rules={[{ required: true, message: '请选择询价表' }]}
                >
                    <Select 
                        placeholder="请选择询价表"
                        onChange={(value) => {
                            // 检查文件类型，如果是图片或文本文件，自动切换到第二种方案
                            const fileExt = value ? value.split('.').pop().toLowerCase() : '';
                            const imageExts = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'gif'];
                            const textExts = ['txt', 'doc', 'docx', 'pdf'];
                            
                            if (imageExts.includes(fileExt) || textExts.includes(fileExt)) {
                                setScheme('scheme2');
                                message.info('检测到图片/文本文件，已自动切换到第二方案');
                            }
                        }}
                    >
                        {inquiryFiles.map(file => (
                            <Option key={file} value={file}>{file}</Option>
                        ))}
                    </Select>
                </Form.Item>
                
                <Form.Item label="参数补全方式">
                    <div>
                        <Switch
                            checked={useDefaultRules}
                            onChange={(checked) => {
                                console.log('🔧 [DEBUG] Switch状态改变:', checked);
                                setUseDefaultRules(checked);
                            }}
                            checkedChildren="使用默认规则"
                            unCheckedChildren="交互式选择"
                        />
                        <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                            {useDefaultRules 
                                ? '当型号缺少参数时，自动使用您设置的默认规则补全'
                                : '当型号缺少参数时，弹出选择框让您手动选择'
                            }
                        </div>
                    </div>
                </Form.Item>
                
                <Form.Item label="选择生成方案">
                    <Radio.Group value={scheme} onChange={(e) => setScheme(e.target.value)}>
                        <Radio.Button value="scheme1">第一方案（原报价表）</Radio.Button>
                        <Radio.Button value="scheme2">第二方案（结构化报价）</Radio.Button>
                    </Radio.Group>
                    <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                        💡 提示：图片文件（.png/.jpg/.jpeg/.bmp/.tiff/.gif）和文本文件（.txt/.doc/.docx/.pdf）会自动使用第二方案生成
                    </div>
                </Form.Item>
                
                <Form.Item>
                    <Button 
                        type="primary" 
                        htmlType="submit" 
                        loading={generating}
                        disabled={!userPriceTable || brandList.length === 0}
                    >
                        {generating ? '生成中...' : scheme === 'scheme2' ? '生成第二方案' : scheme === 'scheme1' ? '生成第一方案' : '生成两种方案'}
                    </Button>
                </Form.Item>
            </Form>

            {/* 交互式选择流程 */}
            {interactiveFlowVisible && currentQuoteParams && (
                <InteractiveQuoteFlow
                    priceFile={currentQuoteParams.price_file}
                    inquiryFile={currentQuoteParams.inquiry_file}
                    company={currentQuoteParams.company}
                    onComplete={handleInteractiveComplete}
                    onCancel={handleInteractiveCancel}
                />
            )}

            {/* 第二方案信息输入对话框 */}
            <Modal
                title="第二方案 - 公司信息设置"
                open={showScheme2Modal}
                onOk={() => scheme2Form.submit()}
                onCancel={handleScheme2Cancel}
                width={600}
                confirmLoading={generating}
            >
                <Form form={scheme2Form} onFinish={handleScheme2Confirm} layout="vertical">
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                label="公司名称"
                                name="company_name"
                                rules={[{ required: true, message: '请输入公司名称' }]}
                            >
                                <Input placeholder="请输入公司名称" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                label="业务联系人"
                                name="business_contact"
                                rules={[{ required: true, message: '请输入业务联系人' }]}
                            >
                                <Input placeholder="请输入业务联系人" />
                            </Form.Item>
                        </Col>
                    </Row>
                    
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                label="联系电话"
                                name="contact_phone"
                                rules={[{ required: true, message: '请输入联系电话' }]}
                            >
                                <Input placeholder="请输入联系电话" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                label="联系邮箱"
                                name="contact_email"
                                rules={[{ required: true, message: '请输入联系邮箱' }]}
                            >
                                <Input placeholder="请输入联系邮箱" />
                            </Form.Item>
                        </Col>
                    </Row>
                    
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                label="客户抬头"
                                name="customer_header"
                                rules={[{ required: true, message: '请输入客户抬头' }]}
                            >
                                <Input placeholder="请输入客户抬头" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                label="收件人"
                                name="recipient"
                                rules={[{ required: true, message: '请输入收件人' }]}
                            >
                                <Input placeholder="请输入收件人" />
                            </Form.Item>
                        </Col>
                    </Row>
                    
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                label="联系方式"
                                name="contact_method"
                                rules={[{ required: true, message: '请输入联系方式' }]}
                            >
                                <Input placeholder="请输入联系方式" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                label="地址"
                                name="address"
                                rules={[{ required: true, message: '请输入地址' }]}
                            >
                                <Input placeholder="请输入地址" />
                            </Form.Item>
                        </Col>
                    </Row>
                    
                    <Form.Item
                        label="税率选择"
                        name="tax_rate"
                        rules={[{ required: true, message: '请选择税率' }]}
                    >
                        <Radio.Group>
                            <Radio value="3%">3%</Radio>
                            <Radio value="13%">13%</Radio>
                            <Radio value="不含税">不含税</Radio>
                        </Radio.Group>
                    </Form.Item>
                </Form>
            </Modal>
        </Card>
    );
};

// 价格表管理组件
const PriceTableManager = ({ onRefresh }) => {
    const [priceTable, setPriceTable] = useState(null);
    const [tableData, setTableData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [editingCell, setEditingCell] = useState(null);
    const [newRowData, setNewRowData] = useState({});
    const [showAddRowModal, setShowAddRowModal] = useState(false);
    const [brands, setBrands] = useState([]);
    
    // 分页相关状态
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(50);
    const [pagination, setPagination] = useState(null);

    // 加载用户的价格表
    const loadUserPriceTable = async () => {
        try {
            setLoading(true);
            const response = await request('/files');
            const data = await response.json();
            const priceFiles = data.price_tables || [];
            
            if (priceFiles.length > 0) {
                // 用户有价格表，加载第一个
                const filename = priceFiles[0];
                setPriceTable(filename);
                await loadTableContent(filename, 1, pageSize);
            } else {
                setPriceTable(null);
                setTableData(null);
                setBrands([]);
            }
        } catch (error) {
            message.error('加载价格表失败');
        } finally {
            setLoading(false);
        }
    };

    // 加载价格表内容
    const loadTableContent = async (filename, page = 1, size = pageSize) => {
        try {
            setLoading(true);
            const response = await request(`/price-table/${encodeURIComponent(filename)}?page=${page}&page_size=${size}`);
            const data = await response.json();
            setTableData(data);
            setPagination(data.pagination);
            setCurrentPage(page);
            setPageSize(size);
            
            // 提取品牌信息 (只在第一页时提取，避免重复)
            if (page === 1) {
                extractBrandsFromTable(data);
            }
        } catch (error) {
            message.error('加载价格表内容失败');
        } finally {
            setLoading(false);
        }
    };

    // 从价格表中提取品牌信息
    const extractBrandsFromTable = (data) => {
        if (!data || !data.columns || !data.data) return;
        
        const brandColumnIndex = data.columns.findIndex(col => 
            col === '品牌' || col.includes('品牌') || col.includes('厂商') || col.includes('厂家')
        );
        
        if (brandColumnIndex !== -1) {
            const brandSet = new Set();
            data.data.forEach(row => {
                if (row[brandColumnIndex] && row[brandColumnIndex].toString().trim()) {
                    brandSet.add(row[brandColumnIndex].toString().trim());
                }
            });
            setBrands(Array.from(brandSet).sort());
        } else {
            setBrands([]);
        }
    };

    // 删除价格表
    const handleDeleteTable = async () => {
        if (!priceTable) return;
        
        try {
            await request(`/price-table/${encodeURIComponent(priceTable)}`, {
                method: 'DELETE'
            });
            message.success('价格表删除成功');
            setPriceTable(null);
            setTableData(null);
            setBrands([]);
            setPagination(null);
            setCurrentPage(1);
            onRefresh && onRefresh();
        } catch (error) {
            message.error('删除价格表失败');
        }
    };

    // 分页处理函数
    const handlePageChange = async (page, size) => {
        if (!priceTable) return;
        await loadTableContent(priceTable, page, size);
    };

    const handlePageSizeChange = async (current, size) => {
        if (!priceTable) return;
        await loadTableContent(priceTable, 1, size);
    };

    // 更新单元格
    const handleCellUpdate = async (rowIndex, columnIndex, value) => {
        try {
            const columnName = tableData.columns[columnIndex];
            const response = await request(`/price-table/${encodeURIComponent(priceTable)}/row/${rowIndex}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ [columnName]: value })
            });
            
            if (response.ok) {
                // 更新本地数据
                const newData = { ...tableData };
                newData.data[rowIndex][columnIndex] = value;
                setTableData(newData);
                
                // 如果是品牌列，重新提取品牌信息
                if (columnName === '品牌' || columnName.includes('品牌') || columnName.includes('厂商') || columnName.includes('厂家')) {
                    extractBrandsFromTable(newData);
                }
                
                message.success('更新成功');
            }
        } catch (error) {
            message.error('更新失败');
        }
        setEditingCell(null);
    };

    // 添加新行
    const handleAddRow = async () => {
        try {
            const response = await request(`/price-table/${encodeURIComponent(priceTable)}/add-row`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newRowData)
            });
            
            if (response.ok) {
                message.success('行添加成功');
                await loadTableContent(priceTable, currentPage, pageSize);
                setNewRowData({});
                setShowAddRowModal(false);
            }
        } catch (error) {
            message.error('添加行失败');
        }
    };

    // 删除行
    const handleDeleteRow = async (rowIndex) => {
        try {
            const response = await request(`/price-table/${encodeURIComponent(priceTable)}/row/${rowIndex}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                message.success('行删除成功');
                await loadTableContent(priceTable, currentPage, pageSize);
            }
        } catch (error) {
            message.error('删除行失败');
        }
    };



    // 删除列
    const handleDeleteColumn = async (columnName) => {
        try {
            const response = await request(`/price-table/${encodeURIComponent(priceTable)}/column/${encodeURIComponent(columnName)}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                message.success('列删除成功');
                await loadTableContent(priceTable, currentPage, pageSize);
            }
        } catch (error) {
            message.error('删除列失败');
        }
    };

    // 保存整个表格
    const handleSaveTable = async () => {
        try {
            const response = await request(`/price-table/${encodeURIComponent(priceTable)}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(tableData)
            });
            
            if (response.ok) {
                message.success('价格表保存成功');
                // 重新提取品牌信息
                extractBrandsFromTable(tableData);
            }
        } catch (error) {
            message.error('保存失败');
        }
    };

    useEffect(() => {
        loadUserPriceTable();
    }, []);

    const renderTableContent = () => {
        if (!tableData) return null;

        return (
            <div style={{ marginTop: 16 }}>
                <div style={{ marginBottom: 16, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                    <Button type="primary" onClick={() => setShowAddRowModal(true)}>
                        ➕ 添加行
                    </Button>
                    <Button type="primary" onClick={handleSaveTable}>
                        💾 保存
                    </Button>
                    <Button onClick={() => loadTableContent(priceTable, currentPage, pageSize)}>
                        🔄 刷新
                    </Button>
                    <Button danger onClick={() => {
                        Modal.confirm({
                            title: '确认删除',
                            content: '确定要删除当前价格表吗？删除后需要重新上传。',
                            onOk: handleDeleteTable
                        });
                    }}>
                        🗑️ 删除价格表
                    </Button>
                </div>

                {/* 品牌信息显示 */}
                {brands.length > 0 && (
                    <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '6px' }}>
                        <strong>📋 当前价格表中的品牌 ({brands.length}个):</strong>
                        <div style={{ marginTop: 8 }}>
                            {brands.map(brand => (
                                <Tag key={brand} color="green" style={{ margin: '2px' }}>{brand}</Tag>
                            ))}
                        </div>
                    </div>
                )}

                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #d9d9d9' }}>
                        <thead>
                            <tr>
                                {tableData.columns.map((column, index) => (
                                    <th key={index} style={{ 
                                        border: '1px solid #d9d9d9', 
                                        padding: '8px', 
                                        backgroundColor: '#fafafa',
                                        position: 'relative'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span>{column}</span>
                                            <Button 
                                                type="text" 
                                                size="small" 
                                                danger
                                                onClick={() => handleDeleteColumn(column)}
                                                style={{ padding: '2px 4px', minWidth: 'auto' }}
                                            >
                                                ×
                                            </Button>
                                        </div>
                                    </th>
                                ))}
                                <th style={{ border: '1px solid #d9d9d9', padding: '8px', backgroundColor: '#fafafa' }}>
                                    操作
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {tableData.data.map((row, rowIndex) => (
                                <tr key={rowIndex}>
                                    {row.map((cell, colIndex) => (
                                        <td key={colIndex} style={{ 
                                            border: '1px solid #d9d9d9', 
                                            padding: '8px',
                                            backgroundColor: editingCell?.row === rowIndex && editingCell?.col === colIndex ? '#fff7e6' : 'white'
                                        }}>
                                            {editingCell?.row === rowIndex && editingCell?.col === colIndex ? (
                                                <Input
                                                    value={cell || ''}
                                                    onChange={(e) => {
                                                        const newData = { ...tableData };
                                                        newData.data[rowIndex][colIndex] = e.target.value;
                                                        setTableData(newData);
                                                    }}
                                                    onPressEnter={() => handleCellUpdate(rowIndex, colIndex, cell)}
                                                    onBlur={() => handleCellUpdate(rowIndex, colIndex, cell)}
                                                    autoFocus
                                                />
                                            ) : (
                                                <div 
                                                    onClick={() => setEditingCell({ row: rowIndex, col: colIndex })}
                                                    style={{ cursor: 'pointer', minHeight: '20px' }}
                                                >
                                                    {cell || ''}
                                                </div>
                                            )}
                                        </td>
                                    ))}
                                    <td style={{ border: '1px solid #d9d9d9', padding: '8px' }}>
                                        <Button 
                                            type="text" 
                                            size="small" 
                                            danger
                                            onClick={() => handleDeleteRow(rowIndex)}
                                        >
                                            删除
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                
                {/* 分页组件 */}
                {pagination && (
                    <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ color: '#666', fontSize: '14px' }}>
                            显示第 {pagination.start_index} - {pagination.end_index} 条，共 {pagination.total_rows} 条记录
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{ fontSize: '14px' }}>每页显示:</span>
                                <Select
                                    value={pageSize}
                                    onChange={(value) => handlePageSizeChange(currentPage, value)}
                                    style={{ width: 80 }}
                                    size="small"
                                >
                                    <Option value={20}>20</Option>
                                    <Option value={50}>50</Option>
                                    <Option value={100}>100</Option>
                                    <Option value={200}>200</Option>
                                </Select>
                                <span style={{ fontSize: '14px' }}>条</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                <Button 
                                    size="small" 
                                    disabled={!pagination.has_prev}
                                    onClick={() => handlePageChange(currentPage - 1, pageSize)}
                                >
                                    上一页
                                </Button>
                                <span style={{ margin: '0 8px', fontSize: '14px' }}>
                                    第 {pagination.current_page} / {pagination.total_pages} 页
                                </span>
                                <Button 
                                    size="small" 
                                    disabled={!pagination.has_next}
                                    onClick={() => handlePageChange(currentPage + 1, pageSize)}
                                >
                                    下一页
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    return (
        <div>
            <Card title="价格表管理" extra={
                <Button onClick={loadUserPriceTable} loading={loading}>
                    🔄 刷新
                </Button>
            }>
                {!priceTable ? (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                        <div style={{ fontSize: '16px', marginBottom: '16px' }}>
                            📋 您还没有上传价格表
                        </div>
                        <div style={{ fontSize: '14px', color: '#666' }}>
                            请先在"文件管理"页面上传价格表，然后在此页面进行编辑管理
                        </div>
                    </div>
                ) : (
                    <div>
                        <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#e6f7ff', border: '1px solid #91d5ff', borderRadius: '6px' }}>
                            <strong>📄 当前价格表: {priceTable}</strong>
                        </div>
                        {renderTableContent()}
                    </div>
                )}
            </Card>

            {/* 添加行模态框 */}
            <Modal
                title="添加新行"
                open={showAddRowModal}
                onOk={handleAddRow}
                onCancel={() => setShowAddRowModal(false)}
            >
                {tableData && (
                    <div>
                        {tableData.columns.map((column, index) => (
                            <div key={index} style={{ marginBottom: 16 }}>
                                <label>{column}:</label>
                                <Input
                                    value={newRowData[column] || ''}
                                    onChange={(e) => setNewRowData({ ...newRowData, [column]: e.target.value })}
                                    placeholder={`请输入${column}`}
                                />
                            </div>
                        ))}
                    </div>
                )}
            </Modal>


        </div>
    );
};

// 主应用组件
const App = () => {
    const [user, setUser] = useState(null);
    const [files, setFiles] = useState({
        price_tables: [],
        inquiry_tables: [],
        quotes: []
    });
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('1');
    const [uploadedBrands, setUploadedBrands] = useState({}); // 存储上传时提取的品牌信息
    
    useEffect(() => {
        const username = localStorage.getItem('username');
        const isAdmin = localStorage.getItem('isAdmin') === 'true';
        if (username) {
            setUser({ username, is_admin: isAdmin });
        }
    }, []);
    
    const loadFiles = async () => {
        if (!user) return;
        
        console.log('🔄 刷新文件列表...');
        setLoading(true);
        try {
            // 添加时间戳参数防止缓存
            const timestamp = new Date().getTime();
            const response = await request(`/files?t=${timestamp}`);
            const data = await response.json();
            console.log('📂 获取到文件列表:', data);
            setFiles(data);
        } catch (error) {
            console.error('❌ 获取文件列表失败:', error);
        } finally {
            setLoading(false);
        }
    };
    
    useEffect(() => {
        if (user) {
            loadFiles();
        }
    }, [user]);
    
    const handleLogin = (userData) => {
        setUser(userData);
    };
    
    const handleLogout = async () => {
        try {
            console.log('🔍 [DEBUG] 用户退出登录');
            
            // 调用后端的logout API清理临时文件
            const token = localStorage.getItem('authToken');
            if (token) {
                console.log('🔍 [DEBUG] 开始调用后端退出API');
                const response = await fetch(`${API_BASE}/logout`, {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Basic ' + token
                    },
                    mode: 'cors',
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('❌ [DEBUG] 服务器端退出失败:', response.status, errorText);
                    throw new Error(`服务器端退出失败: ${response.status} ${errorText}`);
                }
                
                const data = await response.json();
                console.log('✅ [DEBUG] 服务器端退出成功:', data);
                if (data.cleaned_dirs > 0) {
                    message.success(`已清理 ${data.cleaned_dirs} 个临时文件夹`);
                }
            }
        } catch (error) {
            console.error('❌ [DEBUG] 服务器端退出失败:', error);
            message.warning('退出时清理临时文件失败，但您已成功退出登录');
        } finally {
            // 无论服务器端是否成功，都清除本地存储并更新状态
            localStorage.removeItem('authToken');
            localStorage.removeItem('username');
            localStorage.removeItem('isAdmin');
            setUser(null);
            message.success('已退出登录');
        }
    };
    
    if (!user) {
        return <Login onLogin={handleLogin} />;
    }
    
    return (
        <div className="main-container">
            <div className="content-wrapper">
                <div className="header">
                    <Title level={3} style={{ margin: 0 }}>
                        阀门报价系统
                    </Title>
                    <Space>
                        <Text>欢迎，{user.username}</Text>
                        {user.is_admin && <Tag color="gold">管理员</Tag>}
                        <Button onClick={handleLogout}>退出登录</Button>
                    </Space>
                </div>
                
                <div className="section">
                    <Tabs activeKey={activeTab} onChange={setActiveTab}>
                        <TabPane tab="文件管理" key="1">
                            <Space direction="vertical" style={{ width: '100%' }} size="large">
                                <Card title="上传价格表">
                                    <FileUpload 
                                        type="price" 
                                        onSuccess={loadFiles}
                                        onBrandsExtracted={(filename, brands) => {
                                            console.log('🔧 [DEBUG] 接收到品牌信息:', filename, brands);
                                            setUploadedBrands(prev => ({
                                                ...prev,
                                                [filename]: brands
                                            }));
                                        }}
                                    />
                                    <Title level={5} style={{ marginTop: 24 }}>已上传的价格表</Title>
                                    <FileList files={files.price_tables} type="价格表" onRefresh={loadFiles} />
                                </Card>
                                
                                <Card title="上传询价表">
                                    <FileUpload type="inquiry" onSuccess={loadFiles} />
                                    <Title level={5} style={{ marginTop: 24 }}>已上传的询价表</Title>
                                    <FileList files={files.inquiry_tables} type="询价表" onRefresh={loadFiles} />
                                </Card>
                                
                                <Card title="生成的报价单">
                                    <FileList files={files.quotes} type="报价单" onRefresh={loadFiles} />
                                </Card>
                            </Space>
                        </TabPane>
                        
                        <TabPane tab="生成报价" key="2">
                            <QuoteGenerator
                                priceFiles={files.price_tables}
                                inquiryFiles={files.inquiry_tables}
                                onSuccess={loadFiles}
                                uploadedBrands={uploadedBrands}
                            />
                        </TabPane>
                        
                        <TabPane tab="价格表管理" key="3">
                            <PriceTableManager onRefresh={loadFiles} />
                        </TabPane>
                        
                        <TabPane tab="默认规则设置" key="4">
                            <DefaultRulesManagement />
                        </TabPane>
                        
                        {user.is_admin && (
                            <TabPane tab="账户管理" key="5">
                                <AccountManagement />
                            </TabPane>
                        )}
                    </Tabs>
                </div>
            </div>
        </div>
    );
};

// 图标组件
const InboxOutlined = (props) => (
    <svg {...props} viewBox="64 64 896 896" focusable="false" data-icon="inbox" width="1em" height="1em" fill="currentColor">
        <path d="M885.2 446.3l-.2-.8-112.2-285.1c-5-16.1-19.9-27.2-36.8-27.2H288c-17 0-32.1 11.3-36.9 27.6L139.4 443l-.3.7-.2.8c-1.3 4.9-1.7 9.9-1 14.8-.1 1.6-.2 3.2-.2 4.8V830c0 17.7 14.3 32 32 32h684c17.7 0 32-14.3 32-32V464.1c0-1.3 0-2.6-.1-3.9.4-4.9.3-9.9-1-14.9zm-442.8-171.5h225.2l85.6 217.6H544V320.1h73.2v172.3H406.8l85.6-217.6zM832 592H192V562h640v30zm0 198H192v-96h640v96z"/>
    </svg>
);

const DeleteOutlined = (props) => (
    <svg {...props} viewBox="64 64 896 896" focusable="false" data-icon="delete" width="1em" height="1em" fill="currentColor">
        <path d="M360 184h-8c4.4 0 8-3.6 8-8v8h304v-8c0 4.4 3.6 8 8 8h-8v72h72v-80c0-35.3-28.7-64-64-64H352c-35.3 0-64 28.7-64 64v80h72v-72zm504 72H160c-17.7 0-32 14.3-32 32v32c0 4.4 3.6 8 8 8h60.4l24.7 523c1.6 34.1 29.8 61 63.9 61h454c34.2 0 62.3-26.8 63.9-61l24.7-523H888c4.4 0 8-3.6 8-8v-32c0-17.7-14.3-32-32-32zM731.3 840H292.7l-24.2-512h487l-24.2 512z" />
    </svg>
);

// 渲染应用
ReactDOM.render(<App />, document.getElementById('root'));