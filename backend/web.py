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
      .muted{color:#475569;font-size:13px}
      .table-head{font-weight:bold;color:#0f172a}
      @media(max-width:600px){
        .btn{width:100%}
        .section-head{flex-direction:column;align-items:flex-start}
      }
    </style>

    <div class="page">
      <h1 style="color:#fff;margin-bottom:14px">Premier League 数据系统</h1>
      <p style="color:#e3f2fd;margin-bottom:18px">快速查看赛季积分榜；主榜按积分，其余按进球/丢球/净胜。</p>

      <div class="card">
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

      <div class="card">
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

      <div class="card">
        <h3>账户与用户操作</h3>
        <div style="margin:8px 0">
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
        }catch(e){ alert('网络错误: '+e) }
    })

    // 获取当前用户信息
    document.getElementById('getUserInfoBtn').addEventListener('click', async function(){
        const token = localStorage.getItem('token');
        if (!token) {
            alert('请先登录（需token）');
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
        const token = localStorage.getItem('token');
        if (!token) { alert('请先登录'); return; }
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
        const token = localStorage.getItem('token');
        if (!token) { alert('请先登录'); return; }
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
      const select = document.getElementById('seasonSelect');
      select.innerHTML = '';
      try{
        const res = await fetch('/api/seasons');
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
      const season = document.getElementById('seasonSelect').value;
      const status = document.getElementById('standingsStatus');
      const grid = document.getElementById('standingsGrid');
      if(!season){ status.textContent='请先选择赛季'; return; }
      status.textContent = '积分榜加载中...';
      grid.innerHTML = '';
      try{
        const url = `/api/standings?season=${encodeURIComponent(season)}&type=points`;
        const res = await fetch(url);
        const data = await res.json();
        if(!res.ok){ status.textContent = '获取失败: '+(data.error||res.status); return; }
        status.textContent = `${data.count} 支球队 · 赛季 ${data.season} · 积分榜`;
        if(!data.rows || data.rows.length===0){ grid.innerHTML='<div class="muted">暂无数据</div>'; return; }
        grid.innerHTML = data.rows.map((row,index)=>`
          <div class="stat-card">
            <div class="table-head">#${row.position || index+1} · ${row.team}</div>
            <div class="pill" style="margin:8px 0">积分 ${row.points}</div>
            <div class="muted">场次 ${row.played} | 胜 ${row.won} 平 ${row.drawn} 负 ${row.lost}</div>
            <div class="muted">进 ${row.gf} 失 ${row.ga} 净 ${row.gd}</div>
          </div>
        `).join('');
      }catch(e){
        status.textContent = '网络错误: '+e;
      }
    }

    async function fetchOtherBoards(){
      const season = document.getElementById('seasonSelect').value;
      const type = document.getElementById('boardTypeSelect').value;
      const status = document.getElementById('otherBoardsStatus');
      const container = document.getElementById('otherBoards');
      if(!season){ status.textContent='请先选择赛季'; return; }
      status.textContent = '加载中...';
      container.innerHTML = '';

      try{
        const res = await fetch(`/api/standings?season=${encodeURIComponent(season)}&type=${encodeURIComponent(type)}`);
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

    function refreshBoards(){
      fetchStandings();
      fetchOtherBoards();
    }

    document.getElementById('loadStandingsBtn').addEventListener('click', refreshBoards);
    document.getElementById('boardTypeSelect').addEventListener('change', fetchOtherBoards);

    // 初始加载：展示选择弹窗并预取赛季
    window.addEventListener('load', async function(){ 
      setTimeout(()=> showBackdrop('choiceBackdrop'), 150);
      await loadSeasons();
      refreshBoards();
    })
    </script>
    """
