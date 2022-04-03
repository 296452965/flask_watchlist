import unittest

from watchlist import app, db
from watchlist.model import Movie, User
from watchlist.commands import forge, initdb


class WatchlistTestCase(unittest.TestCase):

    def setUp(self):
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATEBASE_URI='sqlite:///:memory:'
        )
        db.create_all()
        user = User(name='Test', username='test')
        user.set_password('123')
        movie = Movie(title='Test Movie Title', year='2019')
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client()
        self.runner = app.test_cli_runner()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_app_exit(self):
        self.assertIsNotNone(app)

    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    def test_404_page(self):
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('返回首页', data)
        self.assertEqual(response.status_code, 404)

    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test的观影单', data)
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)

    def login(self):
        self.client.post('/login', data=dict(
            username='test',
            password='123',
        ), follow_redirects=True)

    def test_creat_item(self):
        self.login()

        response = self.client.post('/', data=dict(
            title='New Movie',
            year='2022'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('添加成功', data)
        self.assertIn('New Movie', data)

        response = self.client.post('/', data=dict(
            title='',
            year='2022'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('添加成功', data)
        self.assertIn('输入不正确', data)

        response = self.client.post('/', data=dict(
            title='New Movie',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('添加成功', data)
        self.assertIn('输入不正确', data)

    # 测试更新条目
    def test_update_item(self):
        self.login()

        # 测试更新页面
        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('编辑电影信息', data)
        self.assertIn('Test Movie Title', data)
        self.assertIn('2019', data)

        # 测试更新条目操作
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('编辑成功', data)
        self.assertIn('New Movie Edited', data)

        # 测试更新条目操作，但电影标题为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('编辑成功', data)
        self.assertIn('输入不正确', data)

        # 测试更新条目操作，但电影年份为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited Again',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('编辑成功', data)
        self.assertNotIn('New Movie Edited Again', data)
        self.assertIn('输入不正确', data)

    # 测试删除条目
    def test_delete_item(self):
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('删除成功', data)
        self.assertNotIn('Test Movie Title', data)

    # 测试登录保护
    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('退出登录', data)
        self.assertNotIn('设置', data)
        self.assertNotIn('<form method="post">', data)
        self.assertNotIn('删除', data)
        self.assertNotIn('编辑', data)

    # 测试登录
    def test_login(self):
        response = self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('登录成功', data)
        self.assertIn('退出登录', data)
        self.assertIn('设置', data)
        self.assertIn('删除', data)
        self.assertIn('编辑', data)
        self.assertIn('<form method="post">', data)

        # 测试使用错误的密码登录
        response = self.client.post('/login', data=dict(
            username='test',
            password='456'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('登录成功', data)
        self.assertIn('用户名或密码错误', data)

        # 测试使用错误的用户名登录
        response = self.client.post('/login', data=dict(
            username='wrong',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('登录成功', data)
        self.assertIn('用户名或密码错误', data)

        # 测试使用空用户名登录
        response = self.client.post('/login', data=dict(
            username='',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('登录成功', data)
        self.assertIn('输入不正确', data)

        # 测试使用空密码登录
        response = self.client.post('/login', data=dict(
            username='test',
            password=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('登录成功', data)
        self.assertIn('输入不正确', data)

    # 测试登出
    def test_logout(self):
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('退出成功', data)
        self.assertNotIn('退出登录', data)
        self.assertNotIn('设置', data)
        self.assertNotIn('删除', data)
        self.assertNotIn('编辑', data)
        self.assertNotIn('<form method="post">', data)

    # 测试设置
    def test_settings(self):
        self.login()

        # 测试设置页面
        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('设置', data)
        self.assertIn('昵称', data)

        # 测试更新设置
        response = self.client.post('/settings', data=dict(
            name='Grey Li',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('设置更新成功', data)
        self.assertIn('Grey Li', data)

        # 测试更新设置，名称为空
        response = self.client.post('/settings', data=dict(
            name='',
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('设置更新成功', data)
        self.assertIn('输入不正确', data)

    def test_forge_command(self):
        result = self.runner.invoke(forge)
        self.assertIn('Done.', result.output)
        self.assertNotEqual(Movie.query.count(), 0)

    # 测试初始化数据库
    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    # 测试生成管理员账户
    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        result = self.runner.invoke(args=['admin', '--username', 'grey', '--password', '123'])
        self.assertIn('Creating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'grey')
        self.assertTrue(User.query.first().validate_password('123'))

    # 测试更新管理员账户
    def test_admin_command_update(self):
        # 使用 args 参数给出完整的命令参数列表
        result = self.runner.invoke(args=['admin', '--username', 'peter', '--password', '456'])
        self.assertIn('Updating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'peter')
        self.assertTrue(User.query.first().validate_password('456'))


if __name__ == "__main__":
    unittest.main()
