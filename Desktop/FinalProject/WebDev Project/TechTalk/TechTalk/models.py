from datetime import datetime
from flask_login import UserMixin
from extensions import db


followers = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), index=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'), index=True)
)


likes = db.Table('likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), index=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), index=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers', lazy='dynamic'
    )
    followers = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='followed', lazy='dynamic'
    )
    sent_follow_requests = db.relationship('FollowRequest', foreign_keys='FollowRequest.sender_id', back_populates='sender', lazy='dynamic')
    received_follow_requests = db.relationship('FollowRequest', foreign_keys='FollowRequest.receiver_id', back_populates='receiver', lazy='dynamic')

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            db.session.commit()

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            db.session.commit()

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def has_liked_post(self, post):
        return post.likes.filter(likes.c.user_id == self.id).count() > 0

    def send_follow_request(self, user):
        if self.is_following(user):
            return False
        existing_request = FollowRequest.query.filter_by(sender_id=self.id, receiver_id=user.id).first()
        if existing_request:
            return False
        follow_request = FollowRequest(sender_id=self.id, receiver_id=user.id)
        db.session.add(follow_request)
        db.session.commit()
        return True

    def accept_follow_request(self, follow_request):
        if follow_request.receiver_id != self.id:
            return False

        sender = follow_request.sender

        if not self.is_following(sender):
            self.follow(sender)

        if not sender.is_following(self):
            sender.follow(self)

        db.session.delete(follow_request)
        db.session.commit()
        
        return True


    def decline_follow_request(self, follow_request):
        if follow_request.receiver_id != self.id:
            return False
        db.session.delete(follow_request)
        db.session.commit()
        return True

    def get_following_count(self):
        return self.followed.count()

    def get_followers_count(self):
        return self.followers.count()

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    image_file = db.Column(db.String(20), nullable=True)
    video_file = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True, index=True)
    comments = db.relationship('Comment', backref='post', lazy=True)
    likes = db.relationship('User', secondary=likes, backref=db.backref('liked_posts', lazy='dynamic'), lazy='dynamic')
    group = db.relationship('Group', backref=db.backref('posts_in_group', lazy=True))  # Changed backref name
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    group = db.relationship('Group', backref=db.backref('posts', lazy=True))

    def like(self, user):
        if not self.has_liked(user):
            self.likes.append(user)
            db.session.commit()

    def unlike(self, user):
        if self.has_liked(user):
            self.likes.remove(user)
            db.session.commit()

    def has_liked(self, user):
        return self.likes.filter(likes.c.user_id == user.id).count() > 0

    def get_comment_count(self):
        return self.comments.count()

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)

    def __repr__(self):
        return f"Comment('{self.date_posted}', '{self.content}')"

class FollowRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_follow_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='received_follow_requests')

    def __repr__(self):
        return f"FollowRequest('{self.sender.username}', '{self.receiver.username}')"

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    members = db.relationship('User', secondary='group_members', backref='groups')
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User', backref='created_groups')

    def __repr__(self):
        return f"Group('{self.name}', '{self.description}')"



class GroupMember(db.Model):
    __tablename__ = 'group_members'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    group = db.relationship('Group', backref=db.backref('group_members', lazy=True))
    user = db.relationship('User', backref=db.backref('group_members', lazy=True))

    def __repr__(self):
        return f"GroupMember('{self.group_id}', '{self.user_id}')"

