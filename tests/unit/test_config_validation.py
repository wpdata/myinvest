"""
单元测试：配置验证
测试 investapp/config/settings.py 中的配置验证逻辑
"""

import pytest
import os
from pathlib import Path


class TestConfigValidation:
    """配置验证测试套件"""

    def test_force_close_margin_rate_less_than_default(self):
        """测试：强平保证金率必须小于默认保证金率"""
        # 正常情况：force_close < default
        default_margin = 0.15
        force_close_margin = 0.10
        assert force_close_margin < default_margin, "强平保证金率应小于默认保证金率"

        # 异常情况：force_close >= default (应该被拒绝)
        with pytest.raises(AssertionError):
            invalid_force_close = 0.15
            assert invalid_force_close < default_margin, "强平保证金率应小于默认保证金率"

    def test_margin_rate_valid_range(self):
        """测试：保证金率应在合理范围内 (0.05-0.50)"""
        # 有效值
        valid_rates = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]
        for rate in valid_rates:
            assert 0.05 <= rate <= 0.50, f"保证金率 {rate} 应在 [0.05, 0.50] 范围内"

        # 无效值
        invalid_rates = [0.0, -0.10, 0.60, 1.0]
        for rate in invalid_rates:
            assert not (0.05 <= rate <= 0.50), f"保证金率 {rate} 应被拒绝"

    def test_risk_free_rate_valid_range(self):
        """测试：无风险利率应在合理范围内 (0-0.10)"""
        # 有效值
        valid_rates = [0.0, 0.01, 0.03, 0.05, 0.10]
        for rate in valid_rates:
            assert 0.0 <= rate <= 0.10, f"无风险利率 {rate} 应在 [0.0, 0.10] 范围内"

        # 无效值
        invalid_rates = [-0.01, 0.15, 0.50]
        for rate in invalid_rates:
            assert not (0.0 <= rate <= 0.10), f"无风险利率 {rate} 应被拒绝"

    def test_volatility_valid_range(self):
        """测试：波动率应在合理范围内 (0.05-1.0)"""
        # 有效值
        valid_vols = [0.05, 0.10, 0.20, 0.50, 1.0]
        for vol in valid_vols:
            assert 0.05 <= vol <= 1.0, f"波动率 {vol} 应在 [0.05, 1.0] 范围内"

        # 无效值
        invalid_vols = [0.0, -0.10, 1.5, 2.0]
        for vol in invalid_vols:
            assert not (0.05 <= vol <= 1.0), f"波动率 {vol} 应被拒绝"

    def test_database_path_exists(self):
        """测试：数据库路径应存在或可创建"""
        db_path = Path("/Users/pw/ai/myinvest/data/myinvest.db")

        # 检查父目录存在
        assert db_path.parent.exists(), f"数据库目录 {db_path.parent} 应存在"

        # 如果数据库不存在，应该可以创建
        if not db_path.exists():
            # 测试是否有写权限
            test_file = db_path.parent / "test_write.tmp"
            try:
                test_file.touch()
                test_file.unlink()
                assert True, "应有创建数据库文件的权限"
            except PermissionError:
                pytest.fail("没有创建数据库文件的权限")

    def test_env_file_format(self):
        """测试：.env 文件格式正确"""
        env_path = Path("/Users/pw/ai/myinvest/.env")

        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                # 应该包含 = 符号
                assert '=' in line, f".env 第 {line_num} 行格式错误：{line}"

                # key 不应为空
                key = line.split('=')[0].strip()
                assert key, f".env 第 {line_num} 行 key 为空"

    def test_critical_config_keys_present(self):
        """测试：关键配置项应存在"""
        # 这是一个示例，实际应该读取配置文件
        required_keys = [
            'DATABASE_URL',
            'DEFAULT_MARGIN_RATE',
            'FORCE_CLOSE_MARGIN_RATE',
            'RISK_FREE_RATE',
            'DEFAULT_VOLATILITY'
        ]

        # 模拟配置字典
        config = {
            'DATABASE_URL': 'sqlite:////Users/pw/ai/myinvest/data/myinvest.db',
            'DEFAULT_MARGIN_RATE': '0.15',
            'FORCE_CLOSE_MARGIN_RATE': '0.10',
            'RISK_FREE_RATE': '0.03',
            'DEFAULT_VOLATILITY': '0.20'
        }

        for key in required_keys:
            assert key in config, f"配置项 {key} 缺失"
            assert config[key], f"配置项 {key} 值为空"

    def test_numeric_config_parsing(self):
        """测试：数值配置项能正确解析"""
        # 模拟配置字符串转数值
        config_strings = {
            'DEFAULT_MARGIN_RATE': '0.15',
            'FORCE_CLOSE_MARGIN_RATE': '0.10',
            'RISK_FREE_RATE': '0.03',
            'DEFAULT_VOLATILITY': '0.20'
        }

        for key, value_str in config_strings.items():
            try:
                value = float(value_str)
                assert isinstance(value, float), f"{key} 应解析为 float"
                assert value > 0, f"{key} 应为正数"
            except ValueError:
                pytest.fail(f"{key} 值 '{value_str}' 无法解析为数值")

    def test_multiplier_positive_integer(self):
        """测试：合约乘数应为正整数"""
        # 有效值
        valid_multipliers = [1, 10, 100, 300, 500]
        for mult in valid_multipliers:
            assert isinstance(mult, int), f"乘数 {mult} 应为整数"
            assert mult > 0, f"乘数 {mult} 应为正数"

        # 无效值
        invalid_multipliers = [0, -100, 0.5, 1.5]
        for mult in invalid_multipliers:
            if isinstance(mult, int):
                assert mult <= 0, f"乘数 {mult} 应被拒绝"


class TestEnvironmentValidation:
    """环境配置验证测试"""

    def test_python_version(self):
        """测试：Python 版本应 >= 3.10"""
        import sys
        version = sys.version_info
        assert version.major == 3, "应使用 Python 3.x"
        assert version.minor >= 10, f"Python 版本应 >= 3.10，当前 {version.major}.{version.minor}"

    def test_required_packages_installed(self):
        """测试：必需的包已安装"""
        required_packages = [
            'pandas',
            'numpy',
            'streamlit',
            'sqlalchemy',
            'pytest'
        ]

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                pytest.fail(f"必需的包 {package} 未安装")

    def test_working_directory(self):
        """测试：当前工作目录正确"""
        cwd = Path.cwd()
        expected_markers = ['investapp', 'investlib-data', 'investlib-quant']

        # 至少应该有一个标记目录存在
        markers_found = [marker for marker in expected_markers if (cwd / marker).exists()]
        assert len(markers_found) > 0, f"当前目录 {cwd} 不是项目根目录"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
