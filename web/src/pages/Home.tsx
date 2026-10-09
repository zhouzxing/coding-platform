import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Home() {
  const { user } = useAuth();
  return (
    <>
      <div className="hero">
        <h1>Coding<span className="accent">Platform</span></h1>
        <p>
          在线编程练习平台。像 LeetCode 一样刷题，代码在浏览器里即时运行，
          提交后由服务端沙箱执行完整测试集，秒级反馈。
        </p>
        <div className="hero-actions">
          {user ? (
            <Link to="/problems"><button className="primary">进入题解</button></Link>
          ) : (
            <>
              <Link to="/problems"><button>浏览题目</button></Link>
              <Link to="/register"><button className="primary">注册并开始</button></Link>
            </>
          )}
        </div>
      </div>
      <div className="feature-grid">
        <div className="feature">
          <h3>🧩 经典算法题</h3>
          <p>Two Sum、Maximum Subarray、Binary Search 等经典题目，含可见样例与隐藏测试。</p>
        </div>
        <div className="feature">
          <h3>⚡ 实时判分</h3>
          <p>代码在浏览器里写，点 Run 立刻跑可见测试；提交后跑完整隐藏测试集，秒级反馈。</p>
        </div>
        <div className="feature">
          <h3>🛡️ 沙箱执行</h3>
          <p>后端用 subprocess + resource.setrlimit 隔离执行，超时 / 内存限制 / 异常捕获全兜底。</p>
        </div>
      </div>
    </>
  );
}
