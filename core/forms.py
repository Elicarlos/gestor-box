from django import forms
from django.contrib.auth.models import User
from .models import Funcionario, Filial, Box, Atividade
import pandas as pd

class FuncionarioForm(forms.ModelForm):
    nome = forms.CharField(
        label='Nome completo',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome completo',
            'autofocus': True
        })
    )
    matricula = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a matrícula'
        })
    )
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a senha'
        }),
        required=True,
        help_text='A senha deve ter pelo menos 8 caracteres, incluindo letras e números'
    )
    confirmar_senha = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme a senha'
        }),
        required=True
    )
    filial = forms.ModelChoiceField(
        queryset=Filial.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=False,
        empty_label="Selecione a filial (opcional)"
    )

    class Meta:
        model = Funcionario
        fields = ['matricula', 'nome', 'senha', 'confirmar_senha', 'filial']

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')

        if senha and confirmar_senha:
            if senha != confirmar_senha:
                raise forms.ValidationError('As senhas não coincidem')
            
            # Validar força da senha
            if len(senha) < 8:
                raise forms.ValidationError('A senha deve ter pelo menos 8 caracteres')
            if not any(c.isalpha() for c in senha):
                raise forms.ValidationError('A senha deve conter pelo menos uma letra')
            if not any(c.isdigit() for c in senha):
                raise forms.ValidationError('A senha deve conter pelo menos um número')

        return cleaned_data

    def save(self, commit=True):
        matricula = self.cleaned_data['matricula']
        nome = self.cleaned_data['nome']
        senha = self.cleaned_data['senha']
        user, created = User.objects.get_or_create(username=matricula, defaults={'first_name': nome})
        if senha:
            user.set_password(senha)
        if not created:
            user.first_name = nome
            if senha:
                user.set_password(senha)
        user.save()
        funcionario = super().save(commit=False)
        funcionario.user = user
        if commit:
            funcionario.save()
        return funcionario

class FuncionarioImportForm(forms.Form):
    file = forms.FileField(label='Arquivo CSV ou Excel')

    def process_file(self):
        file = self.cleaned_data['file']
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            raise forms.ValidationError('Formato de arquivo não suportado. Envie CSV ou Excel.')
        results = {'success': 0, 'fail': 0, 'errors': []}
        for i, row in df.iterrows():
            try:
                matricula = str(row['matricula'])
                nome = str(row['nome'])
                email = str(row.get('email', ''))
                senha = str(row.get('senha', ''))
                filial_nome = str(row.get('filial', ''))
                filial = Filial.objects.filter(nome=filial_nome).first() if filial_nome else None
                user, created = User.objects.get_or_create(username=matricula, defaults={'email': email, 'first_name': nome})
                if senha:
                    user.set_password(senha)
                if not created:
                    user.email = email
                    user.first_name = nome
                    if senha:
                        user.set_password(senha)
                user.save()
                Funcionario.objects.update_or_create(user=user, defaults={
                    'matricula': matricula,
                    'filial': filial,
                })
                results['success'] += 1
            except Exception as e:
                results['fail'] += 1
                results['errors'].append(f'Linha {i+2}: {e}')
        return results

class FilialForm(forms.ModelForm):
    nome = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome da filial'
        })
    )
    cidade = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a cidade'
        })
    )
    uf = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'UF',
            'maxlength': '2'
        })
    )

    class Meta:
        model = Filial
        fields = ['nome', 'cidade', 'uf']

class BoxForm(forms.ModelForm):
    nome = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome do box'
        })
    )
    localizacao = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a localização'
        })
    )
    filial = forms.ModelChoiceField(
        queryset=Filial.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        empty_label="Selecione a filial"
    )

    class Meta:
        model = Box
        fields = ['nome', 'localizacao', 'filial']

class AtividadeForm(forms.ModelForm):
    nome = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome da atividade'
        })
    )
    duracao_estimada = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Duração em minutos'
        })
    )
    filial = forms.ModelChoiceField(
        queryset=Filial.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        empty_label="Selecione a filial"
    )

    class Meta:
        model = Atividade
        fields = ['nome', 'duracao_estimada', 'filial']
