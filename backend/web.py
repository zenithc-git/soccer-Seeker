webui = """
    <style>
      *{box-sizing:border-box}
      body{font-family:Arial,Helvetica,sans-serif;background:linear-gradient(135deg,#0d47a1,#1976d2);color:#0f172a;margin:0;padding:0}
      a{color:#0d47a1}
      h1,h2,h3,p{margin:0}
      .page{max-width:1100px;margin:0 auto;padding:28px 20px 64px}
      .card{background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 12px 34px rgba(0,0,0,0.12);margin-bottom:18px}
      .pill{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;background:#e3f2fd;color:#0d47a1;font-size:12px;font-weight:bold}
      .btn{padding:9px 14px;border:none;border-radius:8px;background:#1976d2;color:#fff;cursor:pointer;font-weight:bold;transition:transform .12s ease,box-shadow .12s ease}
      .btn.secondary{background:#6c757d}
      .btn:active{transform:translateY(1px);box-shadow:0 2px 8px rgba(0,0,0,0.16)}
      .modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,0.5);display:none;align-items:center;justify-content:center}
      .modal{background:#fff;padding:20px;border-radius:12px;max-width:420px;width:92%;box-shadow:0 6px 24px rgba(0,0,0,0.2)}
      .modal h2{margin-top:0}
      .row{margin:8px 0}
      .row input{width:100%;padding:8px;border:1px solid #ccc;border-radius:6px}
      .section-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
      .standings-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:12px}
      .boards-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:12px}
      .stat-card{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px}
      .stat-card h4{margin:0 0 6px;font-size:16px;color:#0f172a}
      .team-card{cursor:pointer;transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease;border:1px solid transparent}
      .team-card:hover{transform:translateY(-2px);box-shadow:0 10px 20px rgba(0,0,0,0.12);border-color:#e0e7ff}
      .muted{color:#475569;font-size:13px}
      .table-head{font-weight:bold;color:#0f172a}
      .record-row{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}
      .record-chip{padding:10px 12px;border-radius:10px;font-weight:bold}
      .record-win{background:#e8f5e9;color:#2e7d32}
      .record-draw{background:#f3f4f6;color:#374151}
      .record-loss{background:#ffebee;color:#c62828}
      .player-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-top:10px}
      .player-chip{background:#e3f2fd;border-radius:10px;padding:8px 10px;color:#0d47a1;font-weight:600}
      .team-modal{max-width:760px;width:95%}
      .badge{display:inline-block;padding:6px 10px;border-radius:10px;font-weight:bold;font-size:12px;background:#e2e8f0;color:#0f172a;margin-right:6px}
      .top-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px;flex-wrap:wrap}
      .user-chip{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:999px;background:#e3f2fd;color:#0d47a1;cursor:pointer;border:1px solid #cbd5e1;box-shadow:0 4px 12px rgba(0,0,0,0.08)}
      .avatar{width:42px;height:42px;border-radius:50%;background:#0d47a1;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;overflow:hidden}
      .avatar img{width:100%;height:100%;object-fit:cover}
      .user-meta{display:flex;flex-direction:column;line-height:1.2}
      .user-meta .role{font-size:12px;color:#475569}
      .user-modal{max-width:520px}
      .user-modal .row label{display:block;margin-bottom:4px;color:#475569;font-size:13px}
      @media(max-width:600px){
        .btn{width:100%}
        .section-head{flex-direction:column;align-items:flex-start}
      }
    </style>

    <div class="page">
      <div class="top-bar">
        <div>
          <h1 style="color:#fff;margin-bottom:6px">Premier League 数据系统</h1>
          <p style="color:#e3f2fd;margin-bottom:6px">快速查看赛季积分榜；主榜按积分，其余按进球/丢球/净胜。</p>
        </div>
        <div id="userBadge" class="user-chip" title="查看账号信息">
          <div class="avatar" id="userBadgeAvatar">G</div>
          <div class="user-meta">
            <span id="userBadgeName">访客</span>
            <span class="role" id="userBadgeRole">未登录</span>
          </div>
        </div>
      </div>

      <div class="card" id="standingsCard">
        <div class="section-head">
          <div>
            <h2>积分榜查询</h2>
            <p class="muted">选择赛季，直接拉取积分榜。其他榜单自动同步。</p>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <select id="seasonSelect" style="padding:9px 10px;border-radius:8px;border:1px solid #cbd5e1;min-width:120px"></select>
            <button id="loadStandingsBtn" class="btn">更新榜单</button>
          </div>
        </div>
        <div id="standingsStatus" class="muted" style="margin-top:10px">等待请求...</div>
        <div id="standingsGrid" class="standings-grid"></div>
      </div>

      <div class="card" id="otherBoardsCard">
        <div class="section-head">
          <div>
            <h2>进球 / 丢球 / 净胜 榜</h2>
            <p class="muted">选择指标，展示该赛季全部球队。</p>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <select id="boardTypeSelect" style="padding:9px 10px;border-radius:8px;border:1px solid #cbd5e1;min-width:140px">
              <option value="goals_for">按进球</option>
              <option value="goals_against">按丢球</option>
              <option value="goal_diff">按净胜</option>
            </select>
          </div>
        </div>
        <div id="otherBoardsStatus" class="muted" style="margin-top:10px">等待请求...</div>
        <div id="otherBoards" class="boards-grid"></div>
      </div>

      <div class="card" id="teamProfileCard">
        <div class="section-head">
          <div>
            <h2 id="teamProfileTitle">Team hub</h2>
            <p class="muted" id="teamProfileSubtitle">Click any team card to view wins/draws/losses and the full squad</p>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <button id="openTeamDetailBtn" class="btn">打开详情页</button>
            <button id="clearTeamProfile" class="btn secondary">清除</button>
          </div>
        </div>
        <div id="teamProfileContent" class="muted">No team selected yet</div>
      </div>
      
      <div class="card" id="teamStatsCard">
          <div class="section-head">
            <div>
              <h2>球队历年数据可视化</h2>
              <p class="muted">选择球队，查看其历年排名、进球、失球、净胜球折线图（由后端Python生成图片）</p>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap">
              <select id="teamSelect" style="padding:9px 10px;border-radius:8px;border:1px solid #cbd5e1;min-width:160px"></select>
              <button id="loadTeamStatsBtn" class="btn">显示球队数据</button>
            </div>
          </div>
          <div id="teamStatsStatus" class="muted" style="margin-top:10px">等待选择球队...</div>
          <div id="teamCharts" style="width:100%;max-width:900px;margin:0 auto;text-align:center">
            <img id="teamStatsImg" style="max-width:100%;display:none" alt="球队历年数据图" />
          </div>
        </div>

      <div class="card">
        <h3>账户与用户操作</h3>
        <div style="margin:8px 0" id="authActions">
          <button id="openChoice" class="btn">开始（选择 注册/登录 ）</button>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px">
          <button id="logoutBtn" class="btn secondary">退出登录</button>
          <button id="getAllUsersBtn" class="btn">查看所有用户</button>
          <button id="getUserInfoBtn" class="btn">获取当前用户信息</button>
          <button id="deleteAccountBtn" class="btn secondary">删除当前用户账号</button>
        </div>
        <div id="userInfoDisplay" class="muted" style="margin-top:12px;white-space:pre-wrap"></div>
      </div>
    </div>

        <!-- Choice modal -->
    <div id="choiceBackdrop" class="modal-backdrop">
      <div class="modal">
        <h2>请登录</h2>
        <p>登录/注册</p>
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
        <div class="row"><input id="reg_name" placeholder="账号名"></div>
        <div class="row"><input id="reg_email" placeholder="邮箱"></div>
        <div class="row"><input id="reg_password" placeholder="密码" type="password"></div>
        <div class="row"><input id="reg_birthday" placeholder="生日 (YYYY-MM-DD)"></div>
        <div class="row"><input id="reg_role" placeholder=权限 (user/vip_user/admin) 默认普通user"></div>
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
        <div class="row"><input id="login_email" placeholder="请输入注册邮箱"></div>
        <div class="row"><input id="login_password" placeholder="密码" type="password"></div>
        <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px">
          <button id="login_cancel" class="btn secondary">取消</button>
          <button id="login_submit" class="btn">提交</button>
        </div>
      </div>
    </div>

    <!-- User info modal -->
    <div id="userModal" class="modal-backdrop">
      <div class="modal user-modal">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
          <div class="avatar" id="userModalAvatar">U</div>
          <div>
            <h3 id="userModalName" style="margin:0"></h3>
            <div class="muted" id="userModalEmail"></div>
            <div class="pill" id="userModalRole">role</div>
          </div>
        </div>
        <div class="row">
          <label>更换头像</label>
          <input type="file" id="avatarFile" accept="image/*">
          <button id="uploadAvatarBtn" class="btn" style="margin-top:8px">上传头像</button>
        </div>
        <div class="row">
          <label>修改密码</label>
          <input id="oldPwdInput" type="password" placeholder="当前密码">
          <input id="newPwdInput" type="password" placeholder="新密码">
          <button id="changePwdBtn" class="btn secondary" style="margin-top:8px">更新密码</button>
        </div>
        <div id="userModalStatus" class="muted" style="margin-top:8px"></div>
        <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px">
          <button id="userModalClose" class="btn secondary">关闭</button>
        </div>
      </div>
    </div>

    <!-- Team detail modal -->
    <div id="teamDetailBackdrop" class="modal-backdrop">
      <div class="modal team-modal">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
          <div>
            <h2 id="teamDetailTitle" style="margin-bottom:6px"></h2>
            <div id="teamDetailBadges" class="muted"></div>
          </div>
          <button id="teamDetailClose" class="btn secondary">关闭</button>
        </div>
        <div id="teamDetailBody" style="margin-top:12px"></div>
      </div>
    </div>

    <script>
// 移除 ECharts CDN 引用

      // 加载所有球队列表
      async function loadTeams(){
        const token = localStorage.getItem('token');
        const select = document.getElementById('teamSelect');
        select.innerHTML = '';
        try{
          // 复用 standings API 拿到所有球队
          const season = document.getElementById('seasonSelect').value;
          if(!season){
            document.getElementById('teamStatsStatus').textContent = '请先选择赛季';
            return;
          }
          const headers = token ? {'Authorization':`Bearer ${token}`} : {};
          const res = await fetch(`/api/standings?season=${encodeURIComponent(season)}&type=points`,{headers});
          const data = await res.json();
          if(!res.ok || !data.rows){
            document.getElementById('teamStatsStatus').textContent = '获取球队失败: '+(data.error||res.status);
            return;
          }
          data.rows.forEach(row=>{
            const opt = document.createElement('option');
            opt.value = row.team;
            opt.textContent = row.team;
            select.appendChild(opt);
          });
        }catch(e){
          document.getElementById('teamStatsStatus').textContent = '网络错误: '+e;
        }
      }

      // 加载并绘制球队历年数据
      async function loadTeamStats(){
        const token = requireAuth();
        if(!token){
          document.getElementById('teamStatsStatus').textContent = '需登录后查看图表';
          return;
        }
        if(!currentUser){
          await fetchCurrentUser();
        }
        if(!isVipUser()){
          document.getElementById('teamStatsStatus').textContent = '仅 VIP/管理员 可查看图表';
          alert('图表仅限 VIP/管理员查看，请使用对应账号登录');
          return;
        }
        const teamName = document.getElementById('teamSelect').value;
        if(!teamName){
          document.getElementById('teamStatsStatus').textContent = '请先选择球队';
          return;
        }
        document.getElementById('teamStatsStatus').textContent = '加载中...';
        const img = document.getElementById('teamStatsImg');
        img.style.display = 'none';
        img.src = '';
        // 加载图片
        img.onload = function(){
          document.getElementById('teamStatsStatus').textContent = '图片加载成功';
          img.style.display = '';
        };
        img.onerror = function(){
          document.getElementById('teamStatsStatus').textContent = '图片加载失败';
          img.style.display = 'none';
        };
        // 带token
        img.src = `/api/team_stats_plot?team_name=${encodeURIComponent(teamName)}&token=${encodeURIComponent(token)}`;
      }

      document.getElementById('loadTeamStatsBtn').addEventListener('click', loadTeamStats);
      document.getElementById('seasonSelect').addEventListener('change', loadTeams);
    // --- Modal helpers ---
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
        if (role && !['user','vip_user','admin'].includes(role)){ alert('角色只能是 user、vip_user 或 admin'); return }
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
            // 登录成功后自动刷新页面，确保所有数据与状态同步
            window.location.reload();
        }catch(e){ alert('网络错误: '+e) }
    })

    // User badge + modal
    document.getElementById('userBadge').addEventListener('click', openUserModal);
    document.getElementById('userModalClose').addEventListener('click', function(){ hideBackdrop('userModal') });
    document.getElementById('userModal').addEventListener('click', function(e){ if(e.target.id === 'userModal') hideBackdrop('userModal'); });
    document.getElementById('uploadAvatarBtn').addEventListener('click', uploadAvatar);
    document.getElementById('changePwdBtn').addEventListener('click', changePassword);

    // 登录/登出按钮显示控制
    function syncAuthUI(){
      const token = localStorage.getItem('token');
      const authActions = document.getElementById('authActions');
      const logoutBtn = document.getElementById('logoutBtn');
      if(token){
        authActions.style.display = 'none';
        logoutBtn.style.display = '';
      }else{
        authActions.style.display = '';
        logoutBtn.style.display = '';
      }
      updateUserBadge();
    }

    let currentUser = null;

    async function fetchCurrentUser(){
      const token = localStorage.getItem('token');
      if(!token){
        currentUser = null;
        return null;
      }
      try{
        const res = await fetch('/api/me',{headers:{'Authorization':`Bearer ${token}`}});
        const data = await res.json();
        if(res.ok){
          currentUser = data;
          updateUserBadge();
          return data;
        }
      }catch(e){}
      currentUser = null;
      updateUserBadge();
      return null;
    }

    function isVipUser(){
      return currentUser && (currentUser.role === 'vip_user' || currentUser.role === 'admin');
    }

    function setAvatar(el, url, nameFallback='G'){
      if(!el) return;
      if(url){
        el.innerHTML = `<img src="${url}" alt="avatar">`;
      }else{
        const initial = (nameFallback && nameFallback[0]) ? nameFallback[0].toUpperCase() : 'G';
        el.textContent = initial;
      }
    }

    function updateUserBadge(){
      const name = currentUser?.name || '访客';
      const role = currentUser?.role || '未登录';
      document.getElementById('userBadgeName').textContent = name;
      document.getElementById('userBadgeRole').textContent = role;
      setAvatar(document.getElementById('userBadgeAvatar'), currentUser?.avatar_url, name);
    }

    // 简易授权获取（带抑制重复弹窗）
    let authPrompted = false;
    function requireAuth(opts = {}){
      const { silent = false } = opts;
      const token = localStorage.getItem('token');
      if(!token){
        if(!silent && !authPrompted){
          authPrompted = true;
          alert('请先登录后再查看数据');
          showBackdrop('choiceBackdrop');
          setTimeout(()=>{ authPrompted = false; }, 400);
        }
        return null;
      }
      return token;
    }

    async function openUserModal(){
      const token = localStorage.getItem('token');
      if(!token){
        alert('请先登录后再查看账号信息');
        showBackdrop('choiceBackdrop');
        return;
      }
      if(!currentUser){
        await fetchCurrentUser();
      }
      if(!currentUser){
        alert('无法获取用户信息，请重新登录');
        return;
      }
      document.getElementById('userModalName').textContent = currentUser.name || '';
      document.getElementById('userModalEmail').textContent = currentUser.email || '';
      document.getElementById('userModalRole').textContent = currentUser.role || '';
      setAvatar(document.getElementById('userModalAvatar'), currentUser.avatar_url, currentUser.name || 'U');
      document.getElementById('userModalStatus').textContent = '';
      showBackdrop('userModal');
    }

    async function uploadAvatar(){
      const token = requireAuth();
      if(!token) return;
      const fileInput = document.getElementById('avatarFile');
      if(!fileInput.files || fileInput.files.length === 0){
        alert('请选择图片');
        return;
      }
      const formData = new FormData();
      formData.append('avatar', fileInput.files[0]);
      try{
        const res = await fetch('/api/me/avatar',{method:'POST',headers:{'Authorization':`Bearer ${token}`},body:formData});
        const data = await res.json();
        if(!res.ok){
          document.getElementById('userModalStatus').textContent = data.error || '上传失败';
          return;
        }
        currentUser = currentUser || {};
        currentUser.avatar_url = data.avatar_url;
        updateUserBadge();
        setAvatar(document.getElementById('userModalAvatar'), data.avatar_url, currentUser.name || 'U');
        document.getElementById('userModalStatus').textContent = '头像已更新';
        fileInput.value = '';
      }catch(e){
        document.getElementById('userModalStatus').textContent = '网络错误: '+e;
      }
    }

    async function changePassword(){
      const token = requireAuth();
      if(!token) return;
      const oldPwd = document.getElementById('oldPwdInput').value;
      const newPwd = document.getElementById('newPwdInput').value;
      if(!oldPwd || !newPwd){
        alert('请输入当前密码与新密码');
        return;
      }
      try{
        const res = await fetch('/api/me/password',{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},body:JSON.stringify({old_password:oldPwd,new_password:newPwd})});
        const data = await res.json();
        if(!res.ok){
          document.getElementById('userModalStatus').textContent = data.error || '修改失败';
          return;
        }
        document.getElementById('userModalStatus').textContent = '密码已更新';
        document.getElementById('oldPwdInput').value = '';
        document.getElementById('newPwdInput').value = '';
      }catch(e){
        document.getElementById('userModalStatus').textContent = '网络错误: '+e;
      }
    }

    // 获取当前用户信息
    document.getElementById('getUserInfoBtn').addEventListener('click', async function(){
        const token = requireAuth();
        if (!token) {
            return;
        }

        try {
            const res = await fetch('/api/me', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const data = await res.json();
            if (!res.ok) {
                alert('获取用户信息失败: ' + (data.error || '未知错误'));
                return;
            }

            document.getElementById('userInfoDisplay').innerText = JSON.stringify(data, null, 2);
        } catch (e) {
            alert('网络请求错误: ' + e.message);
        }
    });

    // 退出登录
    document.getElementById('logoutBtn').addEventListener('click', function(){
        localStorage.removeItem('token');
        alert('已成功退出登录');
        window.location.reload();
    });

    // 查看所有用户
    document.getElementById('getAllUsersBtn').addEventListener('click', async function(){
        const token = requireAuth();
        if (!token) { return; }
        try {
            const res = await fetch('/api/users', {method: 'GET',headers: { "Authorization": `Bearer ${token}` }});
            const data = await res.json();
            if (!res.ok) { alert('请求失败: ' + (data.error || '未知错误')); return; }
            alert('所有用户信息：' + JSON.stringify(data, null, 2));
        } catch (e) {
            alert('网络错误: ' + e.message);
        }
    });

    // 删除当前账号
    document.getElementById('deleteAccountBtn').addEventListener('click', async function(){
        const token = requireAuth();
        if (!token) { return; }
        if (!confirm('确定要删除当前账号吗？此操作不可恢复')) { return; }
        try {
            const res = await fetch('/api/users/me', {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const data = await res.json();
            if (!res.ok) { alert('删除失败: ' + (data.error || '未知错误')); return; }
            alert('账号删除成功');
            localStorage.removeItem('token');
        } catch (e) {
            alert('网络错误: ' + e);
        }
    });

    // --- 赛季下拉 + 榜单 ---
    async function loadSeasons(){
      const token = localStorage.getItem('token');
      const select = document.getElementById('seasonSelect');
      select.innerHTML = '';
      try{
        const headers = token ? {'Authorization':`Bearer ${token}`} : {};
        const res = await fetch('/api/seasons',{headers});
        const data = await res.json();
        if(!res.ok || !data.seasons){
          document.getElementById('standingsStatus').textContent = '获取赛季失败: '+(data.error||res.status);
          return;
        }
        data.seasons.forEach(year=>{
          const opt = document.createElement('option');
          opt.value = year;
          opt.textContent = year;
          select.appendChild(opt);
        });
      }catch(e){
        document.getElementById('standingsStatus').textContent = '网络错误: '+e;
      }
    }

    async function fetchStandings(){
      const token = localStorage.getItem('token');
      const season = document.getElementById('seasonSelect').value;
      const status = document.getElementById('standingsStatus');
      const grid = document.getElementById('standingsGrid');
      if(!season){ status.textContent='Select a season first'; return; }
      status.textContent = 'Loading table...';
      grid.innerHTML = '';
      try{
        const url = `/api/standings?season=${encodeURIComponent(season)}&type=points`;
        const headers = token ? {'Authorization':`Bearer ${token}`} : {};
        const res = await fetch(url,{headers});
        const data = await res.json();
        if(!res.ok){ status.textContent = 'Failed: '+(data.error||res.status); return; }
        status.textContent = `${data.count} 支球队 · 赛季 ${data.season} · 积分榜`;
        if(!data.rows || data.rows.length===0){ grid.innerHTML='<div class="muted">No data</div>'; return; }
        grid.innerHTML = data.rows.map((row,index)=>`
          <div class="stat-card team-card" data-team-id="${row.team_id||''}" data-team-name="${row.team||''}">
            <div class="table-head">#${row.position || index+1} · ${row.team}</div>
            <div class="pill" style="margin:8px 0">积分 ${row.points}</div>
            <div class="muted">场次 ${row.played} | 胜${row.won} 平${row.drawn} 负${row.lost}</div>
            <div class="muted">进球 ${row.gf} 失球 ${row.ga} 净胜球 ${row.gd}</div>
          </div>
        `).join('');
        grid.querySelectorAll('.team-card').forEach(card=>{
          card.addEventListener('click', ()=> openTeamProfile(card.dataset.teamId, card.dataset.teamName));
        });
      }catch(e){
        status.textContent = 'Network error: '+e;
      }
    }

    async function fetchOtherBoards(){
      const token = localStorage.getItem('token');
      const season = document.getElementById('seasonSelect').value;
      const type = document.getElementById('boardTypeSelect').value;
      const status = document.getElementById('otherBoardsStatus');
      const container = document.getElementById('otherBoards');
      if(!season){ status.textContent='请先选择赛季'; return; }
      status.textContent = '加载中...';
      container.innerHTML = '';

      try{
        const headers = token ? {'Authorization':`Bearer ${token}`} : {};
        const res = await fetch(`/api/standings?season=${encodeURIComponent(season)}&type=${encodeURIComponent(type)}`,{headers});
        const data = await res.json();
        if(!res.ok){ status.textContent = '获取失败: '+(data.error||res.status); return; }
        status.textContent = `已更新榜单 · 赛季 ${data.season} · 指标 ${type}`;

        if(!data.rows || data.rows.length===0){
          container.innerHTML = '<div class="stat-card"><div class="muted">暂无数据</div></div>';
          return;
        }
        container.innerHTML = `
          <div class="stat-card">
            <h4>${type === 'goals_for' ? '按进球' : type === 'goals_against' ? '按丢球' : '按净胜'}</h4>
            <div class="muted" style="margin-bottom:6px">
              ${type === 'goals_for' ? '进球最多优先' : type === 'goals_against' ? '丢球最少优先' : '净胜球最多优先'}
            </div>
            ${data.rows.map((row,index)=>`
              <div style="margin:6px 0">
                <div class="table-head">#${row.position || index+1} · ${row.team}</div>
                <div class="muted">积分 ${row.points} | 进 ${row.gf} 失 ${row.ga} 净 ${row.gd}</div>
              </div>
            `).join('')}
          </div>
        `;
      }catch(e){
        status.textContent = '网络错误: '+e;
      }
    }


    let lastTeamData = null;

    function resetTeamProfile(){
      lastTeamData = null;
      document.getElementById('teamProfileTitle').textContent = 'Team hub';
      document.getElementById('teamProfileSubtitle').textContent = 'Click a team to view wins/draws/losses and squad list';
      document.getElementById('teamProfileContent').innerHTML = '<div class="muted">No team selected yet</div>';
      hideTeamDetail();
    }

    async function openTeamProfile(teamId, teamName){
      const token = localStorage.getItem('token');
      const season = document.getElementById('seasonSelect').value;
      const titleEl = document.getElementById('teamProfileTitle');
      const subtitleEl = document.getElementById('teamProfileSubtitle');
      const contentEl = document.getElementById('teamProfileContent');
      titleEl.textContent = teamName || 'Team hub';
      subtitleEl.textContent = 'Loading...';
      contentEl.innerHTML = '<div class="muted">Loading...</div>';
      try{
        const params = new URLSearchParams();
        if(teamId) params.append('team_id', teamId);
        if(teamName) params.append('team_name', teamName);
        if(season) params.append('season', season);
        const headers = token ? {'Authorization':`Bearer ${token}`} : {};
        const res = await fetch(`/api/team_profile?${params.toString()}`,{headers});
        const data = await res.json();
        if(!res.ok){
          subtitleEl.textContent = data.error || 'Failed to load';
          contentEl.innerHTML = '';
          return;
        }
        lastTeamData = data;
        renderTeamProfile(data);
        subtitleEl.textContent = `Season ${data.season || season || ''} | Played ${data.played ?? '-'} | Points ${data.points ?? '-'}`;
        renderTeamDetail(data);
        showTeamDetail();
      }catch(e){
        subtitleEl.textContent = 'Network error: '+e;
        contentEl.innerHTML = '';
      }
    }

    function renderTeamProfile(data){
      const contentEl = document.getElementById('teamProfileContent');
      const players = data.players || [];
      const playerChips = players.length
        ? `<div class="player-grid">${players.map(p=>`<div class="player-chip">${(p.first_name||'').trim()} ${(p.last_name||'').trim()}${p.position?`  - ${p.position}`:''}</div>`).join('')}</div>`
        : '<div class="muted">No player data</div>';
      contentEl.innerHTML = `
        <div class="record-row">
          <div class="record-chip record-win">W ${data.won ?? '-'}</div>
          <div class="record-chip record-draw">D ${data.drawn ?? '-'}</div>
          <div class="record-chip record-loss">L ${data.lost ?? '-'}</div>
        </div>
        <div style="margin-top:6px">
          <h4>Squad (${players.length})</h4>
          ${playerChips}
        </div>
      `;
    }

    function renderTeamDetail(data){
      const titleEl = document.getElementById('teamDetailTitle');
      const badgeEl = document.getElementById('teamDetailBadges');
      const bodyEl = document.getElementById('teamDetailBody');
      titleEl.textContent = data.team || 'Team';
      badgeEl.innerHTML = `
        <span class="badge">Season ${data.season ?? '-'}</span>
        <span class="badge">Rank ${data.position ?? '-'}</span>
        <span class="badge">Points ${data.points ?? '-'}</span>
      `;
      const players = data.players || [];
      bodyEl.innerHTML = `
        <div class="record-row" style="margin-bottom:8px">
          <div class="record-chip record-win">胜 ${data.won ?? '-'}</div>
          <div class="record-chip record-draw">平 ${data.drawn ?? '-'}</div>
          <div class="record-chip record-loss">负 ${data.lost ?? '-'}</div>
        </div>
        <div class="muted" style="margin-bottom:8px">进球 ${data.gf ?? '-'} · 失球 ${data.ga ?? '-'} · 净胜 ${data.gd ?? '-'}</div>
        <h4 style="margin:10px 0 6px">球员名单 (${players.length})</h4>
        <div class="player-grid">
          ${players.map(p=>`<div class="player-chip">${(p.first_name||'').trim()} ${(p.last_name||'').trim()}${p.position?` - ${p.position}`:''}</div>`).join('') || '<div class="muted">暂无球员数据</div>'}
        </div>
      `;
    }

    function showTeamDetail(){
      document.getElementById('teamDetailBackdrop').style.display = 'flex';
    }
    function hideTeamDetail(){
      document.getElementById('teamDetailBackdrop').style.display = 'none';
    }

    document.getElementById('clearTeamProfile').addEventListener('click', resetTeamProfile);
    document.getElementById('openTeamDetailBtn').addEventListener('click', function(){
      if(!lastTeamData){ alert('请先点击积分榜的球队'); return; }
      renderTeamDetail(lastTeamData);
      showTeamDetail();
    });
    document.getElementById('teamDetailClose').addEventListener('click', hideTeamDetail);
    document.getElementById('teamDetailBackdrop').addEventListener('click', function(e){ if(e.target.id === 'teamDetailBackdrop') hideTeamDetail(); });

    function refreshBoards(){
      fetchStandings();
      fetchOtherBoards();
    }

    document.getElementById('loadStandingsBtn').addEventListener('click', refreshBoards);
    document.getElementById('boardTypeSelect').addEventListener('change', function(){ fetchOtherBoards() });

    // 初始加载：直接预取赛季与榜单（无需登录？
    window.addEventListener('load', async function(){ 
      resetTeamProfile();
      const token = localStorage.getItem('token');
      if(token){
        await fetchCurrentUser();
      }
      syncAuthUI();
      await loadSeasons();
      refreshBoards();
      await loadTeams();
    })
    </script>
    """
