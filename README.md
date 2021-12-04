# Architect

## kubernetes

# Mac 安装 kubernetes

 https://www.jianshu.com/p/a6abdc6f76e1

第一步 克隆详细

git clone https://github.com/gotok8s/k8s-docker-desktop-for-mac.git

第二步 进入 k8s-docker-desktop-for-mac项目，拉取镜像

./load_images.sh

第三步 打开docker 配置页面，enable k8s。需要等k8s start一会

 验证
 $ kubectl cluster-info
 $ kubectl get nodes
 $ kubectl describe node

# 安装 Kubernetes Dashboard

    部署 Kubernetes Dashboard
    $ kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/master/aio/deploy/recommended.yaml
   
    #开启本机访问代理
    $ kubectl proxy

    创建Dashboard管理员用户并用token登陆
    # 创建 ServiceAccount kubernetes-dashboard-admin 并绑定集群管理员权限
    $ kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v1.10.1/src/deploy/recommended/kubernetes-dashboard.yaml

    # 获取登陆 token
    $ kubectl -n kubernetes-dashboard describe secret $(kubectl -n kubernetes-dashboard get secret | grep kubernetes-dashboard-admin | awk '{print $1}')

    token:
    eyJhbGciOiJSUzI1NiIsImtpZCI6Im8tRy1ROTZ3MkMxblp2dWdYdHdnSFFRbE9sSkhKTVdMR2l5TDBTbmZJNUEifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJrdWJlcm5ldGVzLWRhc2hib2FyZC10b2tlbi1jZjZ4cCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJrdWJlcm5ldGVzLWRhc2hib2FyZCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50LnVpZCI6ImZiYTk4NzcyLWMyMmEtNDM1Ny04ZDg0LTczNmNmN2YzOWZlMiIsInN1YiI6InN5c3RlbTpzZXJ2aWNlYWNjb3VudDprdWJlcm5ldGVzLWRhc2hib2FyZDprdWJlcm5ldGVzLWRhc2hib2FyZCJ9.lIgU9Y9kxiCydbcQdDLz7MdBKAIchf0s5nDNr7A7n6txI149_vAapTfGBHXYa1YfIHkSua7LQSA_ss2vBybzLrLGfU0Ovb6cP8NgvvjjTE2QoHjLGtYAes2HBy8tDS5wF7VXoC4Ey6GgBNr0q7946z7sy-LPBQ6ewADmusagGuY7780B2qxRYj2MVFlm2zuYOC_5ujq_a7lUFXomwJgA0o1bGgQZCR8BD4uZYMSup78JiAnjlHmsIfYIXkWLiAy7hyojjx3SB3kNvkFYIOVcWjEjN3pqMRDojdKYbM0_R6nPVOTcDjcsd9RDIUm93fpujBmpRCnbRHsMsFPihTpXtg

    通过下面的连接访问 Dashboard: 
    http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/login

