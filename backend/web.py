webui = """
    <style>
      .modal-backdrop {position:fixed;inset:0;background:rgba(0,0,0,0.5);display:none;align-items:center;justify-content:center}
      .modal {background:#fff;padding:20px;border-radius:8px;max-width:420px;width:90%;box-shadow:0 6px 24px rgba(0,0,0,0.2)}
      .modal h2{margin-top:0}
      .row{margin:8px 0}
      .row input{width:100%;padding:8px;border:1px solid #ccc;border-radius:4px}
      .btn{padding:8px 12px;border:none;border-radius:4px;background:#1976d2;color:#fff;cursor:pointer}
      .btn.secondary{background:#6c757d}
    </style>

    <h1>欢迎访问 Premier League 数据系统 API</h1>
    <p>可用接口：</p>
    <ul>
        <li><a href="/api/seasons">/api/seasons</a> 查看所有赛季</li>
        <li>
            <button id="logoutBtn" class="btn">退出登录</button>
        </li>
        <li>
            <button id="getAllUsersBtn" class="btn">查看所有用户</button> 
        </li>
        <li>
            <button id="getUserInfoBtn" class="btn">获取当前用户信息</button> 
        </li>
        <li>
            <button id="deleteAccountBtn" class="btn">删除当前用户账号</button> 
        </li>
        <li>/api/standings?season=xxxx 获取赛季积分榜</li>
    </ul>

    <div style="margin-top:18px">
      <button id="openChoice" class="btn">开始（选择 注册/登录 ）</button>
    </div>

    <!-- Choice modal -->
    <div id="choiceBackdrop" class="modal-backdrop">
      <div class="modal">
        <h2>欢迎</h2>
        <p>请选择：注册新账号 或 直接登录</p>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
          <button id="choiceRegister" class="btn">注册</button>
          <button id="choiceLogin" class="btn secondary">登录</button>
        </div>
      </div>
    </div>

    <!-- Register modal -->
    <div id="registerBackdrop" class="modal-backdrop">
      <div class="modal">
        <h2>注册</h2>
        <div class="row"><input id="reg_name" placeholder="用户名"></div>
        <div class="row"><input id="reg_email" placeholder="邮箱"></div>
        <div class="row"><input id="reg_password" placeholder="密码" type="password"></div>
        <div class="row"><input id="reg_birthday" placeholder="生日 (YYYY-MM-DD)"></div>
        <div class="row"><input id="reg_role" placeholder="角色 (user/vip_user/admin) 默认user"></div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
          <button id="reg_cancel" class="btn secondary">取消</button>
          <button id="reg_submit" class="btn">提交</button>
        </div>
      </div>
    </div>

    <!-- Login modal -->
    <div id="loginBackdrop" class="modal-backdrop">
      <div class="modal">
        <h2>登录</h2>
        <div class="row"><input id="login_email" placeholder="邮箱"></div>
        <div class="row"><input id="login_password" placeholder="密码" type="password"></div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
          <button id="login_cancel" class="btn secondary">取消</button>
          <button id="login_submit" class="btn">登录</button>
        </div>
      </div>
    </div>

    <script>
    function showBackdrop(id){document.getElementById(id).style.display='flex'}
    function hideBackdrop(id){document.getElementById(id).style.display='none'}

    document.getElementById('openChoice').addEventListener('click', function(){ showBackdrop('choiceBackdrop') })
    document.getElementById('choiceRegister').addEventListener('click', function(){ hideBackdrop('choiceBackdrop'); showBackdrop('registerBackdrop') })
    document.getElementById('choiceLogin').addEventListener('click', function(){ hideBackdrop('choiceBackdrop'); showBackdrop('loginBackdrop') })

    // Register handlers
    document.getElementById('reg_cancel').addEventListener('click', function(){ hideBackdrop('registerBackdrop') })
    document.getElementById('reg_submit').addEventListener('click', async function(){
        const name = document.getElementById('reg_name').value.trim()
        const email = document.getElementById('reg_email').value.trim()
        const password = document.getElementById('reg_password').value
        const birthday = document.getElementById('reg_birthday').value.trim()
        const role = document.getElementById('reg_role').value.trim()
        if (!name || !email || !password){ alert('请填写用户名、邮箱和密码'); return }
        try{
            const res = await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,email,password,birthday,role})})
            const data = await res.json()
            if (!res.ok){ alert('注册失败: '+(data.error||JSON.stringify(data))); return }
            alert('注册成功: '+JSON.stringify(data.user))
            hideBackdrop('registerBackdrop')
        }catch(e){ alert('网络错误: '+e) }
    })

    // Login handlers
    document.getElementById('login_cancel').addEventListener('click', function(){ hideBackdrop('loginBackdrop') })
    document.getElementById('login_submit').addEventListener('click', async function(){
        const email = document.getElementById('login_email').value.trim()
        const password = document.getElementById('login_password').value
        if (!email || !password){ alert('请填写邮箱和密码'); return }
        try{
            const res = await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})})
            const data = await res.json()
            if (!res.ok){ alert('登录失败: '+(data.error||JSON.stringify(data))); return }
            localStorage.setItem('token', data.token);
            alert('登录成功，已保存token'); 
            hideBackdrop('loginBackdrop');
        }catch(e){ alert('网络错误: '+e) }
    })

    // 获取当前用户信息的逻辑
    document.getElementById('getUserInfoBtn').addEventListener('click', async function(){
        // 1. 从本地存储读取 Token
        const token = localStorage.getItem('token');
        if (!token) {
            alert('请先登录（需先获取 Token）');
            return;
        }

        try {
            // 2. 发送带 Token 的 GET 请求到 /api/me
            const res = await fetch('/api/me', {
                method: 'GET', // 接口支持的方法（确保后端路由是 GET）
                headers: {
                    'Authorization': `Bearer ${token}` // 关键：携带 Token 认证头
                }
            });

            // 3. 处理响应
            const data = await res.json();
            if (!res.ok) {
                alert('获取用户信息失败: ' + (data.error || '未知错误'));
                return;
            }

            // 4. 成功：展示用户信息（可以自定义展示方式，比如弹窗/页面渲染）
            alert('当前用户信息：' + JSON.stringify(data, null, 2));
            // （可选）也可以把信息渲染到页面上，比如：
            // document.getElementById('userInfoDisplay').innerText = JSON.stringify(data, null, 2);
        } catch (e) {
            alert('网络请求错误: ' + e.message);
        }
    });

    // 退出登录逻辑
    document.getElementById('logoutBtn').addEventListener('click', function(){
        // 清除本地存储的 Token
        localStorage.removeItem('token');
        alert('已成功退出登录');
        // 跳转到首页/登录页
         window.location.reload(); // 刷新页面
    });

    // 查看所有用户请求
    document.getElementById('getAllUsersBtn').addEventListener('click', async function(){
        const token = localStorage.getItem('token');
        if (!token) {
            alert('请先登录');
            return;
        }
        try {
            const res = await fetch('/api/users', {
                method: 'GET',
                headers: { "Authorization": `Bearer ${token}` } // 必须带Token
            });
            const data = await res.json();
            if (!res.ok) {
                alert('请求失败: ' + (data.error || '未知错误'));
                return;
            }
            // 成功展示所有用户
            alert('所有用户信息：' + JSON.stringify(data, null, 2));
        } catch (e) {
            alert('网络错误: ' + e.message);
        }
    });

    // 删除当前用户账号的处理
    document.getElementById('deleteAccountBtn').addEventListener('click', async function(){
        const token = localStorage.getItem('token');
        if (!token) {
            alert('请先登录');
            return;
        }
        if (!confirm('确定要删除当前账号吗？此操作不可恢复！')) {
            return;
        }
        try {
            const res = await fetch('/api/users/me', {
                method: 'DELETE',  // 明确使用DELETE方法
                headers: {
                    'Authorization': `Bearer ${token}`  // 携带登录凭证
                }
            });
            const data = await res.json();
            if (!res.ok) {
                alert('删除失败: ' + (data.error || '未知错误'));
                return;
            }
            alert('账号删除成功！');
            localStorage.removeItem('token');  // 删除本地token
        } catch (e) {
            alert('网络错误: ' + e);
        }
    });

    // Auto-open choice modal on load
    window.addEventListener('load', function(){ setTimeout(()=> showBackdrop('choiceBackdrop'), 150) })
    </script>
    """