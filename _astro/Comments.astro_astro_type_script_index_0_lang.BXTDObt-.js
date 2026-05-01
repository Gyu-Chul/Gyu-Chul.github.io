class E{wrapper;slug;author;form;nicknameInput;contentInput;submitBtn;listEl;loadingEl;errorEl;charCountEl;comments=[];constructor(t){this.wrapper=t,this.slug=t.dataset.slug||"",this.author=t.dataset.author||"",this.form=t.querySelector("#comment-form"),this.nicknameInput=t.querySelector("#nickname-input"),this.contentInput=t.querySelector("#content-input"),this.submitBtn=t.querySelector("#submit-btn"),this.listEl=t.querySelector("#comments-list"),this.loadingEl=t.querySelector("#loading-state"),this.errorEl=t.querySelector("#error-message"),this.charCountEl=t.querySelector("#char-current"),this.init()}init(){this.form.addEventListener("submit",t=>this.handleSubmit(t)),this.contentInput.addEventListener("input",()=>this.updateCharCount()),this.loadComments()}updateCharCount(){this.charCountEl.textContent=String(this.contentInput.value.length)}async loadComments(){try{const e=await(await fetch(`/api/comments/${this.slug}`)).json();this.comments=e.comments||[],this.renderComments(this.comments)}catch(t){console.error("Failed to load comments:",t),this.listEl.innerHTML=`
          <div class="empty-state">
            <div class="empty-state-icon">💬</div>
            댓글을 불러올 수 없습니다.
          </div>
        `}}renderComments(t){if(t.length===0){this.listEl.innerHTML=`
          <div class="empty-state">
            <div class="empty-state-icon">💬</div>
            아직 댓글이 없습니다.<br>첫 댓글을 작성해보세요!
          </div>
        `;return}const e=document.querySelector("#comments-count");e&&(e.textContent=`(${t.length})`);const s=t.filter(n=>!n.parentId),h=t.filter(n=>n.parentId);let o="";s.forEach(n=>{o+=this.renderComment(n,!1),h.filter(r=>r.parentId===n.id).forEach(r=>{o+=this.renderComment(r,!0)})}),this.listEl.innerHTML=o,this.attachCommentEventListeners()}renderComment(t,e){const s=new Date(t.createdAt),o=new Date().getTime()-s.getTime(),n=Math.floor(o/6e4),d=Math.floor(o/36e5),r=Math.floor(o/864e5);let a;if(n<1)a="방금 전";else if(n<60)a=`${n}분 전`;else if(d<24)a=`${d}시간 전`;else if(r<7)a=`${r}일 전`;else{const y=s.getFullYear(),f=String(s.getMonth()+1).padStart(2,"0"),l=String(s.getDate()).padStart(2,"0"),m=String(s.getHours()).padStart(2,"0"),p=String(s.getMinutes()).padStart(2,"0");a=`${y}.${f}.${l} ${m}:${p}`}const c=t.nickname.charAt(0).toUpperCase(),u=t.updatedAt?'<span class="comment-edited">(수정됨)</span>':"";return`
        <div class="comment-item${e?" reply":""}" data-comment-id="${t.id}">
          <div class="comment-header">
            <div class="comment-avatar">${c}</div>
            <div class="comment-meta">
              <span class="comment-nickname">${this.escapeHtml(t.nickname)}${u}</span>
              <span class="comment-date">${a}</span>
            </div>
          </div>
          <div class="comment-content" data-content="${this.escapeHtml(t.content)}">${this.escapeHtml(t.content)}</div>
          <div class="comment-actions">
            ${e?"":`<button class="comment-action-btn reply-btn" data-comment-id="${t.id}">답글</button>`}
            <button class="comment-action-btn edit-btn" data-comment-id="${t.id}">수정</button>
            <button class="comment-action-btn delete delete-btn" data-comment-id="${t.id}">삭제</button>
          </div>
        </div>
      `}attachCommentEventListeners(){this.listEl.querySelectorAll(".reply-btn").forEach(t=>{t.addEventListener("click",e=>{const s=e.target.dataset.commentId;this.showReplyForm(s)})}),this.listEl.querySelectorAll(".edit-btn").forEach(t=>{t.addEventListener("click",e=>{const s=e.target.dataset.commentId;this.showPasswordModal("edit",s)})}),this.listEl.querySelectorAll(".delete-btn").forEach(t=>{t.addEventListener("click",e=>{const s=e.target.dataset.commentId;this.showPasswordModal("delete",s)})})}showReplyForm(t){this.listEl.querySelectorAll(".reply-form").forEach(c=>c.remove());const e=this.listEl.querySelector(`[data-comment-id="${t}"]`);if(!e)return;const h=`
        <div class="reply-form" data-parent-id="${t}">
          <input type="text" class="reply-nickname" placeholder="닉네임" value="${this.escapeHtml("")}" maxlength="50" />
          <textarea class="reply-content" placeholder="답글을 작성해주세요..." maxlength="1000"></textarea>
          <div class="reply-form-actions">
            <button class="reply-form-btn cancel">취소</button>
            <button class="reply-form-btn submit">답글 등록</button>
          </div>
        </div>
      `;e.insertAdjacentHTML("afterend",h);const o=this.listEl.querySelector(`.reply-form[data-parent-id="${t}"]`),n=o.querySelector(".reply-nickname"),d=o.querySelector(".reply-content"),r=o.querySelector(".cancel"),a=o.querySelector(".submit");n.style.cssText=`
        width: 100%;
        background: var(--bg-card, #161616);
        border: 1px solid var(--border, #262626);
        border-radius: 6px;
        padding: 0.75rem;
        color: var(--text, #fafafa);
        font-family: inherit;
        font-size: 0.85rem;
        margin-bottom: 0.75rem;
      `,r.addEventListener("click",()=>o.remove()),a.addEventListener("click",async()=>{const c=n.value.trim(),u=d.value.trim();if(!c||!u){alert("닉네임과 답글 내용을 입력해주세요.");return}localStorage.setItem("comment_nickname",c),a.disabled=!0,a.textContent="등록 중...";try{const i=await fetch(`/api/comments/${this.slug}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({nickname:c,content:u,author:this.author,parentId:t})});if(!i.ok){const y=await i.json();throw new Error(y.error||"답글 작성에 실패했습니다.")}await this.loadComments()}catch(i){alert(i instanceof Error?i.message:"답글 작성에 실패했습니다."),a.disabled=!1,a.textContent="답글 등록"}})}showPasswordModal(t,e){document.querySelectorAll(".password-modal-overlay").forEach(l=>l.remove());const s=this.comments.find(l=>l.id===e);if(!s)return;const h=t==="edit"?"댓글 수정":"댓글 삭제",o=t==="delete"?"confirm delete":"confirm",n=t==="edit"?"수정":"삭제",d=`
        <div class="password-modal-overlay">
          <div class="password-modal">
            <h4>${h}</h4>
            <input type="password" class="password-input" placeholder="패스워드를 입력하세요" />
            <div class="password-modal-error"></div>
            ${t==="edit"?`<textarea class="edit-content" style="width: 100%; min-height: 100px; margin-bottom: 1rem; padding: 0.75rem; background: var(--bg-secondary, #0a0a0a); border: 1px solid var(--border, #262626); border-radius: 8px; color: var(--text, #fafafa); font-family: inherit; font-size: 0.9rem; resize: vertical;">${this.escapeHtml(s.content)}</textarea>`:""}
            <div class="password-modal-actions">
              <button class="password-modal-btn cancel">취소</button>
              <button class="password-modal-btn ${o}">${n}</button>
            </div>
          </div>
        </div>
      `;document.body.insertAdjacentHTML("beforeend",d);const r=document.querySelector(".password-modal-overlay"),a=r.querySelector(".password-input"),c=r.querySelector(".password-modal-error"),u=r.querySelector(".cancel"),i=r.querySelector(".confirm"),y=r.querySelector(".edit-content"),f=()=>r.remove();u.addEventListener("click",f),r.addEventListener("click",l=>{l.target===r&&f()}),i.addEventListener("click",async()=>{const l=a.value;if(!l){c.textContent="패스워드를 입력해주세요.",c.style.display="block";return}i.disabled=!0,i.textContent="처리 중...";try{if(t==="edit"){const m=y?.value.trim();if(!m){c.textContent="수정할 내용을 입력해주세요.",c.style.display="block",i.disabled=!1,i.textContent="수정";return}const p=await fetch(`/api/comments/${this.slug}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({commentId:e,content:m,password:l})});if(!p.ok){const v=await p.json();throw new Error(v.error||"수정에 실패했습니다.")}}else{const m=await fetch(`/api/comments/${this.slug}`,{method:"DELETE",headers:{"Content-Type":"application/json"},body:JSON.stringify({commentId:e,password:l})});if(!m.ok){const p=await m.json();throw new Error(p.error||"삭제에 실패했습니다.")}}f(),await this.loadComments()}catch(m){c.textContent=m instanceof Error?m.message:"처리에 실패했습니다.",c.style.display="block",i.disabled=!1,i.textContent=n}}),a.addEventListener("keypress",l=>{l.key==="Enter"&&i.click()}),a.focus()}escapeHtml(t){const e=document.createElement("div");return e.textContent=t,e.innerHTML}async handleSubmit(t){t.preventDefault();const e=this.nicknameInput.value.trim(),s=this.contentInput.value.trim();if(!e||!s){this.showError("닉네임과 댓글 내용을 입력해주세요.");return}localStorage.setItem("comment_nickname",e),this.submitBtn.disabled=!0;const h=this.submitBtn.querySelector(".btn-text"),o=this.submitBtn.querySelector(".btn-loading");h&&(h.style.display="none"),o&&(o.style.display="inline");try{const n=await fetch(`/api/comments/${this.slug}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({nickname:e,content:s,author:this.author})});if(!n.ok){const d=await n.json();throw new Error(d.error||"댓글 작성에 실패했습니다.")}this.contentInput.value="",this.updateCharCount(),this.hideError(),await this.loadComments()}catch(n){console.error("Failed to post comment:",n),this.showError(n instanceof Error?n.message:"댓글 작성에 실패했습니다.")}finally{this.submitBtn.disabled=!1;const n=this.submitBtn.querySelector(".btn-text"),d=this.submitBtn.querySelector(".btn-loading");n&&(n.style.display="inline"),d&&(d.style.display="none")}}showError(t){this.errorEl.textContent=t,this.errorEl.style.display="flex"}hideError(){this.errorEl.style.display="none"}}document.addEventListener("DOMContentLoaded",()=>{const b=document.querySelector(".comments-wrapper");b&&new E(b)});
