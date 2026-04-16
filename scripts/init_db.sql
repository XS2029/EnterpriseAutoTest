-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS test_enterprise CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE test_enterprise;

-- 创建 users 表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    status ENUM('active', 'locked', 'disabled') DEFAULT 'active',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建 employees 表
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    department VARCHAR(50),
    position VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    status ENUM('在职', '离职') DEFAULT '在职'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建 approvals 表
CREATE TABLE IF NOT EXISTS approvals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant VARCHAR(50) NOT NULL,
    type VARCHAR(30) NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    content TEXT,
    amount DECIMAL(10,2) DEFAULT 0.00,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入 users 测试数据
INSERT INTO users (username, password, status) VALUES
('admin', 'admin123', 'active'),
('test001', '123456', 'active'),
('test002', '123456', 'active'),
('manager01', 'manager123', 'active'),
('locked_user', 'any', 'locked'),
('disabled001', 'any', 'disabled'),
('hr_user', 'hr123', 'active'),
('finance_user', 'finance123', 'active');

-- 插入 employees 测试数据
INSERT INTO employees (name, department, position, phone, email, status) VALUES
('张三', '技术部', '软件工程师', '13800138001', 'zhangsan@company.com', '在职'),
('李四', '市场部', '市场专员', '13800138002', 'lisi@company.com', '在职'),
('王五', '技术部', '测试工程师', '13800138003', 'wangwu@company.com', '在职'),
('赵六', '人事部', 'HRBP', '13800138004', 'zhaoliu@company.com', '在职'),
('孙七', '财务部', '财务分析师', '13800138005', 'sunqi@company.com', '离职'),
('周八', '技术部', '架构师', '13800138006', 'zhouba@company.com', '在职'),
('吴九', '产品部', '产品经理', '13800138007', 'wujiu@company.com', '在职'),
('郑十', '技术部', '前端开发', '13800138008', 'zhengshi@company.com', '在职'),
('陈一', '销售部', '销售代表', '13800138009', 'chenyi@company.com', '在职'),
('林二', '技术部', '运维工程师', '13800138010', 'liner@company.com', '在职'),
('黄三', '市场部', '品牌经理', '13800138011', 'huangsan@company.com', '在职'),
('刘四', '技术部', '后端开发', '13800138012', 'liusi@company.com', '在职'),
('赵五', '人事部', '招聘专员', '13800138013', 'zhaowu@company.com', '在职'),
('钱六', '财务部', '会计', '13800138014', 'qianliu@company.com', '在职'),
('孙八', '产品部', 'UI设计师', '13800138015', 'sunba@company.com', '在职');

-- 插入 approvals 测试数据
INSERT INTO approvals (applicant, type, content, amount, status) VALUES
('test001', 'leave', '年假申请', 5.0, 'approved'),
('test002', 'reimbursement', '差旅费报销', 1280.50, 'pending'),
('admin', 'leave', '事假申请', 2.0, 'pending'),
('manager01', 'reimbursement', '采购申请', 5000.00, 'approved'),
('test001', 'leave', '病假申请', 3.0, 'pending'),
('hr_user', 'reimbursement', '培训费用', 800.00, 'rejected'),
('test002', 'leave', '调休假申请', 1.0, 'approved'),
('finance_user', 'reimbursement', '办公用品', 350.20, 'pending'),
('test001', 'reimbursement', '交通费', 120.00, 'pending'),
('manager01', 'leave', '年假申请', 5.0, 'pending');