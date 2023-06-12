import os
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.handlers.sha2_crypt import sha256_crypt 
from functools import wraps
from werkzeug.utils import secure_filename
from wtforms import FileField








#Kullanıcı giriş dekoratörü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        
            if "logged_in" in session:

                return f(*args, **kwargs) # bizim dashboard fonksiyonun çalışmasına karşılık geliyor.
            else:
                flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
                return redirect(url_for("login"))

    return decorated_function



# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    
    name = StringField("İsim Soyisim", validators=[validators.Length(min = 4, max = 25)]) # Validators ile bu input alanına en az 4 en fazl 25 karakterden oluşan bir şey yazmasını kontrol ediyoruz.
    username = StringField("Kullanıcı Adı", validators=[validators.Length(min = 5, max = 35)])
    email = StringField("Email", validators=[validators.Email(message = "Lütfen geçerli bir email adresi giriniz.")]) # Emaili kontrol etme yapısı...
    password = PasswordField("Parola", validators=[

        validators.DataRequired(message = "Lütfem bir parola belirleyin."),
        validators.EqualTo(fieldname = "confirm",message=
        "Parolanız uyuşmuyor.")
    ])

    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):

    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

app = Flask(__name__) # __name__ ifadesi, Python'da özel bir değişkendir ve bir modülün adını veya çalıştırıldığı ortamı temsil eder.

app.secret_key = "ybblog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""   # Flask ile MySql veritabanını bağlama işlemlerini yaptık.
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor" # sözlük yapısının cursoru


mysql = MySQL(app)

@app.route("/")# URL yolunu ve HTTP isteğini eşleştiririz.
def index():



    # articles = [
        
    #     {"id":1, "title":"Deneme1","content":"Deneme 1 icerik"},
    #     {"id":2, "title":"Deneme2","content":"Deneme 2 icerik"},
    #     {"id":2, "title":"Deneme3","content":"Deneme 3 icerik"}
    # ]

    return render_template("index.html")



@app.route("/about")
def about():

    return render_template("about.html")


@app.route("/articles")
def articles():

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles"

    result = cursor.execute(sorgu)

    if result>0 :

        articles = cursor.fetchall()


        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")




@app.route("/dashboard")
@login_required
def dashboard():

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0 :
        
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        
        return render_template("dashboard.html")





#Kayıt olma
@app.route("/register", methods=['GET', 'POST'])
def register():

    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate(): # formda sıkıntı yoksa true dönücek ve döngüye girecek.

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)" # aşağıdaki demetin içindeki değerler %s in yerine geçiyor.

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        cursor.close()

        # Bilgileri veri tabanına kaydettik.

        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login")) # fonksiyon yardımıyla hangi urlye gitmek istediğimizi belirttik. mesela bu şekilde kök dizine gitmiş olacak.


    else:
        return render_template("register.html",form = form)
    

#Login işlemi
@app.route("/login",methods = ["GET","POST"])
def login():

    form = LoginForm(request.form)

    if request.method == "POST":
        
        username = form.username.data
        
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * from users where username = %s"

        result = cursor.execute(sorgu,(username,)) # Değer dönerse result 0 dan farklı bir değer olacak. eğer dönmezse yani öyle bir kullanıcı yoksa 0 olacak.

        if result > 0:
            data = cursor.fetchone() # Kullanıcının bütün bilgilerini aldık.

            real_password = data["password"]

            if sha256_crypt.verify(password_entered, real_password):
                flash("Başarıyla giriş yaptınız.","success")
                
                
                session["logged_in"] = True
                session["username"] = username
                
                
                return redirect(url_for("index"))

            else:
                flash("Parolanızı Yanlış Girdiniz.","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor.","danger")
            return redirect(url_for("login"))



    return render_template("login.html",form = form)


@app.route("/article/<string:id>")
def article(id):

    cursor = mysql.connection.cursor()

    sorgu = "select * from articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()

        return render_template("article.html", article = article)
    else:
        return render_template("article.html")




#logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))




@app.route("/article/<string:id>") # Dinamik bir url yapısı oluşturduk <string:id> ile.
def detail(id):
    return "Article id:" + id


#Makale ekleme
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():

    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content =  form.content.data

        cursor =  mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("Makale başarıyla eklendi.","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)


#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        
        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok.")

        return redirect(url_for("index"))

#Makale Güncelleme
@app.route("/edit/<string:id>", methods = ["GET","POST"])
@login_required
def update(id):

    if request.method == "GET":
        
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where id = %s and author = %s"

        result = cursor.execute(sorgu,(id,session["username"]))

        if result==0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()

            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]

            return render_template("update.html",form = form)

    else:
        # POST REQUEST KISMI
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Makale başarıyla güncellendi.","success")
        return redirect(url_for("dashboard"))
    


# Makale Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max = 100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])

#Arama URL
@app.route("/search",methods = ["GET","POST"]) # GET linkle gidilen POST interaktif şekilde gidilen.
def search():

    if request.method == "GET":

        return redirect(url_for("index"))

    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı.","warning")
            return redirect(url_for("articles"))
        
        else:
            articles = cursor.fetchall()

            return render_template("articles.html",articles = articles)







if __name__ == "__main__": # bu şekilde python dosyası terminalden mi çalıştırılmış yoksa bir python modülü olarak mı aktarılmış bunu görüyoruz.
    app.run(debug=True)


